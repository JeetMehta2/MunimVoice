import pytest
import uuid
import datetime as dt
from sqlmodel import Session, select
from app.core.database import engine
from app.models.entities import Campaign, Approval, AuditLogEntry
from app.agent.executor import MunimAgent
from app.agent.tools import TOOL_REGISTRY
from app.agent.guardrails import GuardrailService
from app.sim.uplift_simulator import CampaignUpliftSimulator

def test_agent_tool_dispatch_and_spoken_reply():
    merchant_id = "merchant_sharma_chai"
    
    # 1. Ask about today's sales
    resp = MunimAgent.run(merchant_id, "Aaj kitni bikri hui?")
    assert resp["tool_called"] == "get_daily_summary"
    assert "₹" in resp["spoken_reply"]
    assert "UPI" in resp["spoken_reply"]
    assert len(resp["spoken_reply"].split(".")) <= 3  # Max 2 short spoken sentences

    # 2. Ask about udhaar
    resp_udhaar = MunimAgent.run(merchant_id, "Udhaar kiska baki hai?")
    assert resp_udhaar["tool_called"] == "list_udhaar"
    assert "udhaar" in resp_udhaar["spoken_reply"].lower()

def test_guardrails_tier2_and_budget_cap():
    merchant_id = "merchant_sharma_chai"
    test_key = f"test_idem_{uuid.uuid4().hex[:8]}"

    with Session(engine) as session:
        # Tier 2 Action: Schedule Campaign
        res = GuardrailService.process_action(
            session=session,
            merchant_id=merchant_id,
            action_name="START_CAMPAIGN",
            risk_tier=2,
            payload={"budget": 500.0, "campaign_name": "Test Chai Offer"},
            idempotency_key=test_key
        )
        assert res["status"] == "PENDING_APPROVAL"
        assert res["risk_tier"] == 2
        approval_id = res["approval_id"]

        # Duplicate submission with same idempotency key
        dup_res = GuardrailService.process_action(
            session=session,
            merchant_id=merchant_id,
            action_name="START_CAMPAIGN",
            risk_tier=2,
            payload={"budget": 500.0},
            idempotency_key=test_key
        )
        assert "already submitted" in dup_res["message"].lower()

        # Budget Cap Check (Budget 3500 > 2000 cap)
        cap_res = GuardrailService.process_action(
            session=session,
            merchant_id=merchant_id,
            action_name="START_CAMPAIGN",
            risk_tier=2,
            payload={"budget": 3500.0},
            idempotency_key=f"cap_{uuid.uuid4().hex[:8]}"
        )
        assert cap_res["status"] == "REJECTED_BUDGET_EXCEEDED"

def test_end_to_end_flow_why_low_to_offer_to_approval_to_uplift():
    """
    Acceptance Test for Phase 3:
    End-to-end flow: 'Why were sales low?' -> cause -> offer -> approval -> uplift simulation.
    """
    merchant_id = "merchant_sharma_chai"

    # Step 1: Merchant asks why sales were low
    query = "Sales kyu gir gayi thi pichle hafte?"
    diag = MunimAgent.run(merchant_id, query)
    assert diag["tool_called"] in ("explain_dip", "find_opportunities")
    assert len(diag["spoken_reply"]) > 10

    # Step 2: System proposes a campaign offer for the lull window
    camp_result = TOOL_REGISTRY["schedule_campaign"](
        merchant_id=merchant_id,
        offer_text="Tuesday Special: Chai + Samosa combo pe 20% discount (2 PM - 5 PM)",
        discount_pct=20.0,
        audience_count=35,
        budget=400.0
    )
    assert camp_result["status"] == "PENDING_APPROVAL"
    approval_id = camp_result["approval_id"]
    campaign_id = camp_result["payload"]["campaign_id"]

    # Step 3: Merchant approves the action (Taps 'Haan')
    with Session(engine) as session:
        approval_res = GuardrailService.resolve_approval(
            session=session,
            merchant_id=merchant_id,
            approval_id=approval_id,
            decision="APPROVED",
            actor="merchant"
        )
        assert approval_res["status"] == "APPROVED"
        assert approval_res["execution_result"] is not None
        assert approval_res["execution_result"]["status"] == "DISPATCHED_SIMULATED"

        # Verify Audit Log entry exists
        audit_entry = session.exec(
            select(AuditLogEntry).where(AuditLogEntry.action == "APPROVED_START_CAMPAIGN")
        ).first()
        assert audit_entry is not None
        assert audit_entry.risk_tier == 2

    # Step 4: Run counterfactual uplift measurement with holdout group
    with Session(engine) as session:
        uplift = CampaignUpliftSimulator.run_simulation(session, campaign_id=campaign_id)
        assert uplift["simulated"] is True
        assert uplift["treatment_audience"] > 0
        assert uplift["holdout_audience"] > 0
        assert "uplift_pct" in uplift
        assert "uplift_range" in uplift
        assert uplift["did_work"] is True
        assert uplift["uplift_pct"] > 0
