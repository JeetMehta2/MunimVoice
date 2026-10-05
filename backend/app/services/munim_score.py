import datetime as dt
from typing import Dict, Any, List, Optional
from sqlmodel import Session, select
from app.models.entities import Transaction, Customer, UdhaarRecord, CashLog, ScoreSnapshot

# Configurable score factor weights summing to 100
DEFAULT_SCORE_WEIGHTS = {
    "consistency": 25.0,        # Daily transaction stability & active days
    "growth": 20.0,             # Month-over-month volume/revenue growth
    "repeat_rate": 20.0,        # Loyalty & repeat customer percentage
    "udhaar_recovery": 20.0,    # Ratio of on-time/recovered credit vs delinquent
    "cash_discipline": 15.0     # Frequency of daily bahi-khata logging
}

SCORE_DISCLAIMER = "Illustrative signal for Paytm's existing underwriting, not a credit decision."

class MunimScoreService:
    """
    Transparent 5-factor weighted credit signal formula (0-100).
    Configurable, explainable, and independently testable.
    """

    @classmethod
    def calculate_consistency_score(
        cls, 
        session: Session, 
        merchant_id: str, 
        max_points: float = 25.0
    ) -> float:
        """
        Factor 1 (25 pts): Active trading days ratio over last 30 days.
        """
        now = dt.date(2026, 9, 19)
        start_date = now - dt.timedelta(days=30)
        start_dt = dt.datetime.combine(start_date, dt.time.min)

        txns = session.exec(
            select(Transaction.ts).where(
                Transaction.merchant_id == merchant_id,
                Transaction.ts >= start_dt
            )
        ).all()
        active_days = len({t.date() for t in txns})
        ratio = min(1.0, active_days / 28.0)
        return round(ratio * max_points, 1)

    @classmethod
    def calculate_growth_score(
        cls, 
        session: Session, 
        merchant_id: str, 
        max_points: float = 20.0
    ) -> float:
        """
        Factor 2 (20 pts): Month-over-month revenue trend.
        """
        now = dt.date(2026, 9, 19)
        m1_start = dt.datetime.combine(now - dt.timedelta(days=30), dt.time.min)
        m2_start = dt.datetime.combine(now - dt.timedelta(days=60), dt.time.min)

        txns_m1 = session.exec(
            select(Transaction.amount).where(
                Transaction.merchant_id == merchant_id,
                Transaction.ts >= m1_start
            )
        ).all()
        txns_m2 = session.exec(
            select(Transaction.amount).where(
                Transaction.merchant_id == merchant_id,
                Transaction.ts >= m2_start,
                Transaction.ts < m1_start
            )
        ).all()

        rev_m1 = sum(txns_m1)
        rev_m2 = sum(txns_m2)

        if rev_m2 <= 0:
            return round(max_points * 0.75, 1)

        growth_rate = (rev_m1 - rev_m2) / rev_m2
        # Normal growth between -5% and +15% maps between 10 and 20 pts
        norm_score = max_points * min(1.0, max(0.2, 0.75 + (growth_rate * 1.5)))
        return round(norm_score, 1)

    @classmethod
    def calculate_repeat_score(
        cls, 
        session: Session, 
        merchant_id: str, 
        max_points: float = 20.0
    ) -> float:
        """
        Factor 3 (20 pts): Percentage of repeat customers (visits >= 3).
        """
        customers = session.exec(
            select(Customer).where(Customer.merchant_id == merchant_id)
        ).all()
        if not customers:
            return round(max_points * 0.7, 1)

        repeats = sum(1 for c in customers if c.total_visits >= 3)
        rate = repeats / len(customers)
        return round(min(1.0, rate * 1.8) * max_points, 1)

    @classmethod
    def calculate_udhaar_score(
        cls, 
        session: Session, 
        merchant_id: str, 
        max_points: float = 20.0
    ) -> float:
        """
        Factor 4 (20 pts): Ratio of healthy/recovered udhaar vs critical overdue (>15 days).
        """
        udhaars = session.exec(
            select(UdhaarRecord).where(UdhaarRecord.merchant_id == merchant_id)
        ).all()
        if not udhaars:
            return max_points  # No bad debt

        today = dt.date(2026, 9, 19)
        overdue_15_count = sum(
            1 for u in udhaars 
            if u.due_date and (today - u.due_date).days >= 15 and u.status == "PENDING"
        )
        total_count = len(udhaars)
        healthy_ratio = max(0.0, (total_count - overdue_15_count) / total_count)
        return round(healthy_ratio * max_points, 1)

    @classmethod
    def calculate_cash_discipline_score(
        cls, 
        session: Session, 
        merchant_id: str, 
        max_points: float = 15.0
    ) -> float:
        """
        Factor 5 (15 pts): Days with recorded cash log in last 30 days.
        """
        now = dt.date(2026, 9, 19)
        cutoff = now - dt.timedelta(days=30)
        logs = session.exec(
            select(CashLog).where(
                CashLog.merchant_id == merchant_id,
                CashLog.date >= cutoff
            )
        ).all()
        days_logged = len({l.date for l in logs})
        ratio = min(1.0, days_logged / 25.0)
        return round(ratio * max_points, 1)

    @classmethod
    def evaluate_merchant_score(
        cls, 
        session: Session, 
        merchant_id: str,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Computes the complete 0-100 Munim Score breakdown, actionable advice, and indicative limit.
        """
        w = weights or DEFAULT_SCORE_WEIGHTS
        consistency = cls.calculate_consistency_score(session, merchant_id, w["consistency"])
        growth = cls.calculate_growth_score(session, merchant_id, w["growth"])
        repeat = cls.calculate_repeat_score(session, merchant_id, w["repeat_rate"])
        udhaar = cls.calculate_udhaar_score(session, merchant_id, w["udhaar_recovery"])
        cash = cls.calculate_cash_discipline_score(session, merchant_id, w["cash_discipline"])

        total_score = round(consistency + growth + repeat + udhaar + cash, 1)
        total_score = min(100.0, max(0.0, total_score))

        # Illustrative indicative limit band (scaled by score)
        # E.g. score 78 -> ₹65,000 to ₹85,000
        base_limit = 25000.0 + (total_score * 750.0)
        limit_min = round(base_limit * 0.85, -3)
        limit_max = round(base_limit * 1.15, -3)

        # What will raise it
        advice = []
        if udhaar < w["udhaar_recovery"] * 0.8:
            advice.append("Overdue udhaar recover karein (+5 pts).")
        if cash < w["cash_discipline"] * 0.8:
            advice.append("Rozana cash hisab log karein (+4 pts).")
        if consistency < w["consistency"] * 0.8:
            advice.append("Slow Tuesday slot par sales badhayein (+3 pts).")
        if not advice:
            advice.append("Business metrics mazboot hain. Consistency banaye rakhein.")

        recommendation_text = " ".join(advice)

        # Persist snapshot
        today = dt.date(2026, 9, 19)
        existing_snap = session.exec(
            select(ScoreSnapshot).where(
                ScoreSnapshot.merchant_id == merchant_id,
                ScoreSnapshot.date == today
            )
        ).first()
        if not existing_snap:
            existing_snap = ScoreSnapshot(
                merchant_id=merchant_id,
                date=today,
                score=total_score,
                consistency_score=consistency,
                growth_score=growth,
                repeat_score=repeat,
                udhaar_score=udhaar,
                cash_score=cash,
                indicative_limit_min=limit_min,
                indicative_limit_max=limit_max,
                recommendation=recommendation_text
            )
            session.add(existing_snap)
        else:
            existing_snap.score = total_score
            existing_snap.consistency_score = consistency
            existing_snap.growth_score = growth
            existing_snap.repeat_score = repeat
            existing_snap.udhaar_score = udhaar
            existing_snap.cash_score = cash
            existing_snap.indicative_limit_min = limit_min
            existing_snap.indicative_limit_max = limit_max
            existing_snap.recommendation = recommendation_text
            session.add(existing_snap)
        session.commit()

        return {
            "merchant_id": merchant_id,
            "date": str(today),
            "score": total_score,
            "factors": {
                "consistency": {"score": consistency, "max": w["consistency"], "label": "Business Consistency"},
                "growth": {"score": growth, "max": w["growth"], "label": "Month-over-Month Growth"},
                "repeat_rate": {"score": repeat, "max": w["repeat_rate"], "label": "Customer Loyalty"},
                "udhaar_recovery": {"score": udhaar, "max": w["udhaar_recovery"], "label": "Udhaar Recovery Discipline"},
                "cash_discipline": {"score": cash, "max": w["cash_discipline"], "label": "Daily Bahi-Khata Logging"}
            },
            "indicative_limit_min": limit_min,
            "indicative_limit_max": limit_max,
            "indicative_limit_band": f"₹{int(limit_min):,} - ₹{int(limit_max):,}",
            "what_raises_it": advice,
            "recommendation": recommendation_text,
            "disclaimer": SCORE_DISCLAIMER,
            "simulated": True  # Mandatory simulated badge
        }
