import datetime as dt
from typing import Dict, Any, List, Optional
import numpy as np
from sqlmodel import Session, select
from app.models.entities import Transaction

# Cooldown cache in memory: {merchant_id: last_alert_timestamp}
_LAST_ALERT_TIME: Dict[str, dt.datetime] = {}
COOLDOWN_SECONDS = 300  # 5 minutes cooldown between alerts in production/demo

class FootfallService:
    """
    Real-time footfall sensor computed strictly from UPI payment frequency.
    Calculates rate baselines per hour-of-week, detects surges (Z > 2.0) and lulls.
    """

    @classmethod
    def get_hourly_baseline(
        cls, 
        session: Session, 
        merchant_id: str, 
        day_of_week: int, 
        hour: int
    ) -> Dict[str, float]:
        """
        Computes historical mean (txns/hour) and std dev for a specific (day_of_week, hour).
        """
        # Fetch all transactions matching day_of_week and hour
        txns = session.exec(
            select(Transaction.ts).where(
                Transaction.merchant_id == merchant_id,
                Transaction.status == "SUCCESS"
            )
        ).all()

        # Group by specific date to count txns in that (day_of_week, hour) bucket
        date_counts: Dict[dt.date, int] = {}
        for t in txns:
            if t.weekday() == day_of_week and t.hour == hour:
                d = t.date()
                date_counts[d] = date_counts.get(d, 0) + 1

        if not date_counts:
            return {"mean": 4.0, "std": 1.5}

        counts = list(date_counts.values())
        mean_val = float(np.mean(counts))
        std_val = float(np.std(counts)) if len(counts) > 1 else 1.5
        return {
            "mean": round(mean_val, 2),
            "std": round(max(0.5, std_val), 2)
        }

    @classmethod
    def analyze_live_rate(
        cls, 
        session: Session, 
        merchant_id: str, 
        now: Optional[dt.datetime] = None
    ) -> Dict[str, Any]:
        """
        Evaluates payments in the last 15 minutes, extrapolates hourly rate, computes Z-score.
        """
        if now is None:
            latest = session.exec(
                select(Transaction.ts).where(Transaction.merchant_id == merchant_id).order_by(Transaction.ts.desc())
            ).first()
            now = latest if latest else dt.datetime.utcnow()

        window_start = now - dt.timedelta(minutes=15)
        recent_txns = session.exec(
            select(Transaction).where(
                Transaction.merchant_id == merchant_id,
                Transaction.ts >= window_start,
                Transaction.ts <= now,
                Transaction.status == "SUCCESS"
            )
        ).all()

        recent_count = len(recent_txns)
        # Extrapolate to 1-hour rate
        current_hourly_rate = recent_count * 4.0

        baseline = cls.get_hourly_baseline(session, merchant_id, now.weekday(), now.hour)
        mean_rate = baseline["mean"]
        std_rate = baseline["std"]

        z_score = round((current_hourly_rate - mean_rate) / std_rate, 2)

        # Check cooldown
        last_alert = _LAST_ALERT_TIME.get(merchant_id)
        cooldown_active = (last_alert is not None and (now - last_alert).total_seconds() < COOLDOWN_SECONDS)

        status = "NORMAL"
        announcement = None
        action_suggested = None

        if z_score >= 2.0:
            status = "RUSH"
            announcement = "Dhyan dein: Rush aa raha hai! Doodh aur snacks ka stock check kar lo."
            action_suggested = "prep_stock"
            if not cooldown_active:
                _LAST_ALERT_TIME[merchant_id] = now
        elif z_score <= -1.5 or (recent_count == 0 and mean_rate > 5.0):
            status = "LULL"
            announcement = "Footfall dheemi hai. Kya 15% off ka flash offer chalu karein?"
            action_suggested = "propose_flash_offer"
            if not cooldown_active:
                _LAST_ALERT_TIME[merchant_id] = now

        return {
            "merchant_id": merchant_id,
            "timestamp": now.isoformat(),
            "status": status,
            "current_rate_per_hour": current_hourly_rate,
            "expected_mean_rate": mean_rate,
            "z_score": z_score,
            "announcement": announcement,
            "action_suggested": action_suggested,
            "cooldown_active": cooldown_active
        }

    @classmethod
    def inject_simulated_burst(
        cls, 
        session: Session, 
        merchant_id: str, 
        count: int = 15, 
        amount: float = 20.0
    ) -> Dict[str, Any]:
        """
        Demo tool: Injects an instant burst of simulated payments in the current window.
        Triggers a live Rush detection event (Z > 2.0).
        """
        # Find latest transaction time or use current time
        latest = session.exec(
            select(Transaction.ts).where(Transaction.merchant_id == merchant_id).order_by(Transaction.ts.desc())
        ).first()
        now = (latest + dt.timedelta(minutes=2)) if latest else dt.datetime.utcnow()

        new_txns = []
        for i in range(count):
            sec_offset = i * 20
            txn_time = now - dt.timedelta(seconds=sec_offset)
            txn = Transaction(
                id=f"burst_{merchant_id[:3]}_{int(txn_time.timestamp())}_{i}",
                merchant_id=merchant_id,
                customer_id=None,
                amount=amount,
                ts=txn_time,
                status="SUCCESS",
                settlement_ts=txn_time + dt.timedelta(days=1),
                settlement_delayed=False
            )
            new_txns.append(txn)

        session.add_all(new_txns)
        session.commit()

        # Reset cooldown to allow instant trigger for demo
        _LAST_ALERT_TIME.pop(merchant_id, None)

        # Run analysis immediately
        analysis = cls.analyze_live_rate(session, merchant_id, now)
        return {
            "injected_count": count,
            "analysis": analysis
        }
