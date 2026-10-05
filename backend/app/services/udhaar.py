import uuid
import datetime as dt
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from app.models.entities import UdhaarRecord
from app.agent.guardrails import GuardrailService

class UdhaarService:
    """
    Dedicated Udhaar module managing ledger, aging calculations, and 3-tone reminders.
    All reminders are Tier 2 (require explicit merchant approval) and route through UPI Collect adapter.
    """

    @classmethod
    def add_entry(
        cls, 
        session: Session, 
        merchant_id: str, 
        customer_name: str, 
        amount: float, 
        due_days: int = 7
    ) -> Dict[str, Any]:
        due_date = dt.date.today() + dt.timedelta(days=due_days)
        record = UdhaarRecord(
            merchant_id=merchant_id,
            customer_name=customer_name,
            amount=amount,
            created_at=dt.datetime.utcnow(),
            due_date=due_date,
            status="PENDING",
            reminder_history="[]"
        )
        session.add(record)
        session.commit()
        return {
            "id": record.id,
            "customer_name": record.customer_name,
            "amount": record.amount,
            "due_date": str(record.due_date),
            "status": record.status
        }

    @classmethod
    def get_ledger(cls, session: Session, merchant_id: str) -> List[Dict[str, Any]]:
        """
        Returns all udhaar records with aging status:
          - Current (due in future)
          - Overdue 1-7 days
          - Overdue 8-14 days
          - Overdue 15+ days (flagged private to merchant)
        """
        records = session.exec(
            select(UdhaarRecord).where(UdhaarRecord.merchant_id == merchant_id)
        ).all()
        today = dt.date.today()

        ledger = []
        for r in records:
            if r.due_date and today > r.due_date:
                days_overdue = (today - r.due_date).days
            else:
                days_overdue = 0

            # Aging tier
            if days_overdue >= 15:
                aging_tier = "CRITICAL_15_PLUS"
            elif days_overdue >= 8:
                aging_tier = "OVERDUE_8_14"
            elif days_overdue >= 1:
                aging_tier = "OVERDUE_1_7"
            else:
                aging_tier = "CURRENT"

            ledger.append({
                "id": r.id,
                "customer_name": r.customer_name,
                "amount": r.amount,
                "created_at": r.created_at.strftime("%Y-%m-%d"),
                "due_date": str(r.due_date),
                "days_overdue": days_overdue,
                "aging_tier": aging_tier,
                "is_critical": (days_overdue >= 15),  # Private flag for merchant view
                "status": r.status,
                "reminders_count": len(r.get_reminders())
            })
        return ledger

    @classmethod
    def draft_reminder_message(
        cls, 
        customer_name: str, 
        amount: float, 
        tone: str = "soft"
    ) -> str:
        """
        Drafts a reminder message in merchant's selected tone: soft, firm, funny.
        """
        if tone == "firm":
            return (
                f"Namaste {customer_name} ji, aapka ₹{int(amount)} ka hisab overdue ho chuka hai. "
                f"Kripya diye gaye Paytm UPI link se aaj hi payment clear kar dein."
            )
        elif tone == "funny":
            return (
                f"Arrey {customer_name} bhai! Chai ki charcha aur dosti toh chalti rahegi, "
                f"par ₹{int(amount)} ka hisab bhi clear kar do toh mazaa aa jaye! 😊"
            )
        else:  # soft (default)
            return (
                f"Namaste {customer_name} ji, aasha hai aap kushal mangal hain. "
                f"Aapke dukaan hisab ka ₹{int(amount)} baki hai. Samay milne par settle kar dijiye. Shukriya!"
            )

    @classmethod
    def create_reminder_action(
        cls,
        session: Session,
        merchant_id: str,
        udhaar_id: int,
        tone: str = "soft"
    ) -> Dict[str, Any]:
        """
        Creates a Tier 2 approval action to dispatch UPI Collect payment request.
        """
        rec = session.exec(select(UdhaarRecord).where(UdhaarRecord.id == udhaar_id)).first()
        if not rec:
            return {"error": "Udhaar record not found"}

        message = cls.draft_reminder_message(rec.customer_name, rec.amount, tone)
        payload = {
            "udhaar_id": rec.id,
            "customer_name": rec.customer_name,
            "amount": rec.amount,
            "tone": tone,
            "message": message,
            "notice_text": f"{rec.customer_name} ke ₹{int(rec.amount)} reminder ka draft ban gaya hai."
        }
        idempotency_key = f"udhaar_rem_{rec.id}_{int(rec.amount)}_{dt.date.today().isoformat()}"

        return GuardrailService.process_action(
            session=session,
            merchant_id=merchant_id,
            action_name="SEND_UDHAAR_REMINDER",
            risk_tier=2,
            payload=payload,
            idempotency_key=idempotency_key
        )
