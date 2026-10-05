import json
import uuid
import datetime as dt
from typing import Dict, Any, Optional, Tuple
from sqlmodel import Session, select
from app.models.entities import Approval, Campaign, UdhaarRecord
from app.adapters.mock_adapters import (
    AuditLogger, 
    MockSoundboxAdapter, 
    MockUPICollectAdapter, 
    MockMessagingAdapter,
    get_guardrail_token_for_executor
)

MAX_CAMPAIGN_BUDGET = 2000.0  # Cap for micro-merchants

class GuardrailService:
    """
    Tiered guardrail and action execution layer.
    Exact tiers:
      - Tier 0: read/analyze tools (automatic)
      - Tier 1: drafts (automatic, never blocked)
      - Tier 2: anything that messages customers or spends merchant money (explicit approval required)
    
    Security: Only GuardrailService possesses the execution token to invoke mock adapters.
    """

    @classmethod
    def process_action(
        cls,
        session: Session,
        merchant_id: str,
        action_name: str,
        risk_tier: int,
        payload: Dict[str, Any],
        idempotency_key: str,
        actor: str = "agent"
    ) -> Dict[str, Any]:
        """
        Validates idempotency, budget caps, and applies tier rules.
        """
        # 1. Idempotency Check: prevent duplicate actions
        existing_approval = session.exec(
            select(Approval).where(Approval.idempotency_key == idempotency_key)
        ).first()
        if existing_approval:
            return {
                "status": "PENDING_APPROVAL" if existing_approval.status in ("PENDING", "PENDING_APPROVAL") else existing_approval.status,
                "approval_id": existing_approval.id,
                "risk_tier": existing_approval.risk_tier,
                "message": "Action already submitted (Idempotency cache hit).",
                "simulated": True
            }

        # 2. Budget Cap Validation for Tier 2 spend actions
        if action_name in ("START_CAMPAIGN", "SCHEDULE_CAMPAIGN"):
            budget = float(payload.get("budget", 500.0))
            if budget > MAX_CAMPAIGN_BUDGET:
                AuditLogger.log(
                    session, merchant_id, actor, f"REJECTED_{action_name}",
                    risk_tier, {"reason": f"Budget {budget} exceeds cap {MAX_CAMPAIGN_BUDGET}"},
                    idempotency_key
                )
                return {
                    "status": "REJECTED_BUDGET_EXCEEDED",
                    "message": f"Budget ₹{budget} exceeds maximum allowed cap of ₹{MAX_CAMPAIGN_BUDGET}."
                }

        # 3. Tier 0 & Tier 1: Auto-execute / Draft (Never blocked)
        if risk_tier == 0:
            AuditLogger.log(session, merchant_id, actor, action_name, 0, payload, idempotency_key)
            return {
                "status": "AUTO_EXECUTED",
                "risk_tier": 0,
                "message": f"Tier 0 analysis {action_name} executed."
            }
        elif risk_tier == 1:
            AuditLogger.log(session, merchant_id, actor, action_name, 1, payload, idempotency_key)
            return {
                "status": "DRAFT_CREATED",
                "risk_tier": 1,
                "message": f"Tier 1 draft {action_name} auto-created (not blocked)."
            }

        # 4. Tier 2: Outbound actions (messaging or spending) -> Strict Approval Required
        approval = Approval(
            merchant_id=merchant_id,
            actor=actor,
            action=action_name,
            risk_tier=2,
            payload=json.dumps(payload),
            idempotency_key=idempotency_key,
            status="PENDING_APPROVAL"
        )
        session.add(approval)
        session.commit()

        AuditLogger.log(session, merchant_id, actor, f"APPROVAL_REQUESTED_{action_name}", 2, payload, idempotency_key)

        # If this action triggers a Soundbox notice that requires a decision:
        # Instruction rule: announcement text MUST end with "Phone pe approve kar dijiye"
        token = get_guardrail_token_for_executor()
        if payload.get("notify_soundbox"):
            notice_text = f"{payload.get('notice_text', 'Naya offer taiyar hai.')} Phone pe approve kar dijiye."
            MockSoundboxAdapter.announce(merchant_id, notice_text, _auth_token=token)

        return {
            "status": "PENDING_APPROVAL",
            "approval_id": approval.id,
            "risk_tier": 2,
            "action": action_name,
            "payload": payload,
            "message": "Tier 2 Action requires merchant approval on phone app."
        }

    @classmethod
    def resolve_approval(
        cls,
        session: Session,
        merchant_id: str,
        approval_id: int,
        decision: str,  # "APPROVED" | "REJECTED"
        actor: str = "merchant"
    ) -> Dict[str, Any]:
        """
        Resolves a Tier 2 pending approval.
        Only upon explicit approval is the private token used to execute the mock adapter.
        """
        approval = session.exec(select(Approval).where(Approval.id == approval_id)).first()
        if not approval:
            return {"error": "Approval request not found"}

        if approval.status not in ("PENDING", "PENDING_APPROVAL"):
            return {"status": approval.status, "message": f"Approval was already {approval.status}."}

        approval.status = decision
        approval.resolved_at = dt.datetime.utcnow()
        session.add(approval)
        session.commit()

        payload = json.loads(approval.payload)

        # Log to immutable audit trail
        AuditLogger.log(
            session, merchant_id, actor, f"{decision}_{approval.action}", 
            2, {"approval_id": approval_id, "payload": payload}, approval.idempotency_key
        )

        execution_result = None
        if decision == "APPROVED":
            token = get_guardrail_token_for_executor()
            if approval.action in ("START_CAMPAIGN", "SCHEDULE_CAMPAIGN"):
                campaign = session.exec(
                    select(Campaign).where(Campaign.id == payload.get("campaign_id"))
                ).first()
                if campaign:
                    campaign.status = "ACTIVE"
                    session.add(campaign)
                    session.commit()
                execution_result = MockMessagingAdapter.send_campaign_offer(
                    merchant_id, 
                    payload.get("campaign_name", "Offer"), 
                    payload.get("audience_count", 25), 
                    payload.get("offer_text", ""),
                    _auth_token=token
                )
            elif approval.action == "SEND_UDHAAR_REMINDER":
                execution_result = MockUPICollectAdapter.send_collect_request(
                    merchant_id,
                    payload.get("customer_name", "Customer"),
                    payload.get("amount", 0.0),
                    payload.get("message", "Payment reminder"),
                    _auth_token=token
                )
            elif approval.action == "SOUNDBOX_ANNOUNCE":
                execution_result = MockSoundboxAdapter.announce(
                    merchant_id, 
                    payload.get("message", ""),
                    payload.get("audio"),
                    _auth_token=token
                )

        return {
            "approval_id": approval_id,
            "status": decision,
            "action": approval.action,
            "execution_result": execution_result,
            "simulated": True
        }

    @classmethod
    def announce_to_soundbox(cls, merchant_id: str, text: str, audio: Optional[str] = None) -> Dict[str, Any]:
        """
        Output-only announcement through Soundbox via authorized gateway.
        """
        token = get_guardrail_token_for_executor()
        return MockSoundboxAdapter.announce(merchant_id, text, audio, _auth_token=token)
