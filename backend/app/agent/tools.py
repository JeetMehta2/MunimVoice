import json
import uuid
import datetime as dt
from typing import Dict, Any, List, Optional
from sqlmodel import Session, select
from app.core.database import engine
from app.models.entities import (
    Merchant, Customer, Transaction, CashLog, Expense, 
    UdhaarRecord, Campaign, Opportunity, ScoreSnapshot
)
from app.services.metrics import MetricsService
from app.services.item_inference import ItemInferenceService
from app.services.opportunities import OpportunityService
from app.sim.uplift_simulator import CampaignUpliftSimulator
from app.agent.guardrails import GuardrailService
from app.adapters.mock_adapters import MockMessagingAdapter

def get_daily_summary(merchant_id: str, target_date: Optional[str] = None) -> Dict[str, Any]:
    """Get total UPI revenue, cash-in, expenses, and true daily net profit for a given date."""
    d = dt.date.fromisoformat(target_date) if target_date else None
    with Session(engine) as session:
        return MetricsService.get_daily_summary(session, merchant_id, d)

def get_revenue_trend(merchant_id: str, days: int = 14) -> List[Dict[str, Any]]:
    """Get daily revenue trend breakdown (UPI vs Cash) for the past N days."""
    with Session(engine) as session:
        return MetricsService.get_revenue_trend(session, merchant_id, days)

def get_heatmap(merchant_id: str) -> List[Dict[str, Any]]:
    """Get day-of-week and hourly footfall/revenue distribution matrix."""
    with Session(engine) as session:
        return MetricsService.get_hourly_heatmap(session, merchant_id)

def get_product_mix(merchant_id: str) -> List[Dict[str, Any]]:
    """Get inferred item mix and modal price points without reading ground truth."""
    with Session(engine) as session:
        return ItemInferenceService.infer_product_mix(session, merchant_id)

def find_opportunities(merchant_id: str) -> List[Dict[str, Any]]:
    """Detect slow slots, churned customers, underperforming high-margin items, cashflow gaps, and overdue udhaar."""
    with Session(engine) as session:
        return OpportunityService.detect_all_opportunities(session, merchant_id)

def explain_dip(merchant_id: str, target_date: str) -> Dict[str, Any]:
    """Check if a sales dip was caused by external shocks (rain, cricket match, festivals) and whether to suppress discounting."""
    d = dt.date.fromisoformat(target_date)
    with Session(engine) as session:
        return OpportunityService.explain_dip(session, merchant_id, d)

def log_cash_expense(
    merchant_id: str, 
    cash_in: float = 0.0, 
    expense_category: Optional[str] = None, 
    expense_amount: float = 0.0, 
    expense_desc: Optional[str] = None,
    log_date: Optional[str] = None
) -> Dict[str, Any]:
    """Log daily cash received or business expense (bahi-khata ritual)."""
    d = dt.date.fromisoformat(log_date) if log_date else dt.date.today()
    with Session(engine) as session:
        if cash_in > 0:
            c = session.exec(select(CashLog).where(CashLog.merchant_id == merchant_id, CashLog.date == d)).first()
            if not c:
                c = CashLog(merchant_id=merchant_id, date=d, cash_in=cash_in, source_text="Voice/chat logged")
                session.add(c)
            else:
                c.cash_in = cash_in
                session.add(c)

        if expense_amount > 0 and expense_category:
            exp = Expense(
                merchant_id=merchant_id,
                date=d,
                category=expense_category,
                amount=expense_amount,
                source_text=expense_desc or f"{expense_category} expense"
            )
            session.add(exp)

        session.commit()
        return MetricsService.get_daily_summary(session, merchant_id, d)

def add_udhaar(merchant_id: str, customer_name: str, amount: float, due_days: int = 7) -> Dict[str, Any]:
    """Log a new customer credit / udhaar entry."""
    with Session(engine) as session:
        due = dt.date.today() + dt.timedelta(days=due_days)
        u = UdhaarRecord(
            merchant_id=merchant_id,
            customer_name=customer_name,
            amount=amount,
            due_date=due,
            status="PENDING"
        )
        session.add(u)
        session.commit()
        return {"id": u.id, "customer_name": customer_name, "amount": amount, "due_date": str(due), "status": "PENDING"}

def list_udhaar(merchant_id: str) -> List[Dict[str, Any]]:
    """List all pending customer udhaar records with aging status."""
    with Session(engine) as session:
        records = session.exec(select(UdhaarRecord).where(UdhaarRecord.merchant_id == merchant_id)).all()
        today = dt.date.today()
        result = []
        for r in records:
            overdue_days = (today - r.due_date).days if r.due_date and today > r.due_date else 0
            is_overdue_15 = (overdue_days >= 15)
            result.append({
                "id": r.id,
                "customer_name": r.customer_name,
                "amount": r.amount,
                "created_at": r.created_at.strftime("%Y-%m-%d"),
                "due_date": str(r.due_date),
                "status": r.status,
                "overdue_days": overdue_days,
                "is_overdue_15_plus": is_overdue_15
            })
        return result

def draft_reminder(merchant_id: str, customer_name: str, tone: str = "soft") -> Dict[str, Any]:
    """Draft a polite customer payment reminder in soft, firm, or funny Hinglish tone."""
    with Session(engine) as session:
        rec = session.exec(
            select(UdhaarRecord).where(
                UdhaarRecord.merchant_id == merchant_id,
                UdhaarRecord.customer_name == customer_name,
                UdhaarRecord.status == "PENDING"
            )
        ).first()
        amt = rec.amount if rec else 500.0

    if tone == "firm":
        text = f"Namaste {customer_name} ji, aapka ₹{int(amt)} ka baki hisab pichle hafte se overdue hai. Kripya aaj hi Paytm UPI se settle karein."
    elif tone == "funny":
        text = f"Arrey {customer_name} bhai! Chai ki mithaas aur dosti barkarar rahe, bas ₹{int(amt)} ka chhota hisab clear kar dijiye!"
    else:  # soft
        text = f"Namaste {customer_name} ji, aasha hai sab badhiya hai. Ek chhota sa reminder aapke ₹{int(amt)} ke bahi-khata hisab ke liye. Shukriya!"

    return {
        "customer_name": customer_name,
        "amount": amt,
        "tone": tone,
        "draft_message": text,
        "action_required": "APPROVAL_REQUIRED_TO_SEND"
    }

def propose_offer(
    merchant_id: str, 
    offer_text: str, 
    discount_pct: float, 
    window: Optional[str] = None
) -> Dict[str, Any]:
    """Create a draft customer campaign offer awaiting merchant approval."""
    return {
        "merchant_id": merchant_id,
        "offer_text": offer_text,
        "discount_pct": discount_pct,
        "window": window or "Immediate",
        "risk_tier": 2,
        "approval_needed": True
    }

def request_approval(merchant_id: str, action_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Submit a Tier 2 action for merchant approval (Tap or Voice)."""
    idempotency_key = payload.get("idempotency_key") or str(uuid.uuid4())
    with Session(engine) as session:
        return GuardrailService.process_action(
            session=session,
            merchant_id=merchant_id,
            action_name=action_name,
            risk_tier=2,
            payload=payload,
            idempotency_key=idempotency_key
        )

def schedule_campaign(
    merchant_id: str, 
    offer_text: str, 
    discount_pct: float, 
    audience_count: int = 25, 
    budget: float = 500.0,
    opportunity_id: Optional[int] = None
) -> Dict[str, Any]:
    """Create a campaign record and request Tier 2 merchant approval."""
    with Session(engine) as session:
        camp = Campaign(
            merchant_id=merchant_id,
            opportunity_id=opportunity_id,
            name=f"Campaign: {offer_text[:30]}",
            offer_text=offer_text,
            discount_pct=discount_pct,
            audience_count=audience_count,
            budget=budget,
            status="PENDING_APPROVAL"
        )
        session.add(camp)
        session.commit()

        idempotency_key = f"camp_{camp.id}_{int(budget)}"
        payload = {
            "campaign_id": camp.id,
            "campaign_name": camp.name,
            "offer_text": offer_text,
            "discount_pct": discount_pct,
            "audience_count": audience_count,
            "budget": budget
        }
        return GuardrailService.process_action(
            session=session,
            merchant_id=merchant_id,
            action_name="START_CAMPAIGN",
            risk_tier=2,
            payload=payload,
            idempotency_key=idempotency_key
        )

def send_message(merchant_id: str, recipient: str, message: str) -> Dict[str, Any]:
    """Mock send outbound customer message (simulated)."""
    return MockMessagingAdapter.send_campaign_offer(
        merchant_id=merchant_id,
        campaign_name="Direct Outreach",
        recipient_count=1,
        offer_text=f"To {recipient}: {message}"
    )

def get_munim_score(merchant_id: str) -> Dict[str, Any]:
    """Get latest Munim business score (0-100) and factor breakdown."""
    with Session(engine) as session:
        snapshot = session.exec(
            select(ScoreSnapshot).where(ScoreSnapshot.merchant_id == merchant_id).order_by(ScoreSnapshot.date.desc())
        ).first()
        if snapshot:
            return {
                "score": snapshot.score,
                "consistency": snapshot.consistency_score,
                "growth": snapshot.growth_score,
                "repeat_rate": snapshot.repeat_score,
                "udhaar_recovery": snapshot.udhaar_score,
                "cash_discipline": snapshot.cash_score,
                "indicative_limit_band": f"₹{int(snapshot.indicative_limit_min)} - ₹{int(snapshot.indicative_limit_max)}",
                "recommendation": snapshot.recommendation,
                "simulated": True,
                "disclaimer": "Munim Score is an illustrative signal for Paytm's existing underwriting, not a credit decision."
            }
        return {"score": 75.0, "simulated": True, "disclaimer": "Illustrative signal only."}

def simulate_uplift(campaign_id: int) -> Dict[str, Any]:
    """Run counterfactual simulation for an approved campaign with holdout group."""
    with Session(engine) as session:
        return CampaignUpliftSimulator.run_simulation(session, campaign_id)

TOOL_REGISTRY = {
    "get_daily_summary": get_daily_summary,
    "get_revenue_trend": get_revenue_trend,
    "get_heatmap": get_heatmap,
    "get_product_mix": get_product_mix,
    "find_opportunities": find_opportunities,
    "explain_dip": explain_dip,
    "log_cash_expense": log_cash_expense,
    "add_udhaar": add_udhaar,
    "list_udhaar": list_udhaar,
    "draft_reminder": draft_reminder,
    "propose_offer": propose_offer,
    "request_approval": request_approval,
    "schedule_campaign": schedule_campaign,
    "send_message": send_message,
    "get_munim_score": get_munim_score,
    "simulate_uplift": simulate_uplift
}
