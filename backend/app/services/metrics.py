import datetime as dt
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sqlmodel import Session, select
from app.models.entities import Transaction, Customer, CashLog, Expense, UdhaarRecord

class MetricsService:
    """
    Deterministic financial and operational metrics service.
    Zero LLM arithmetic. All calculations performed strictly in Python.
    """

    @staticmethod
    def get_daily_summary(
        session: Session, 
        merchant_id: str, 
        target_date: Optional[dt.date] = None
    ) -> Dict[str, Any]:
        """
        Calculates UPI sales, cash in, expenses, and true daily net profit.
        """
        if target_date is None:
            latest_txn = session.exec(
                select(Transaction).where(Transaction.merchant_id == merchant_id).order_by(Transaction.ts.desc())
            ).first()
            target_date = latest_txn.ts.date() if latest_txn else dt.date.today()

        start_dt = dt.datetime.combine(target_date, dt.time.min)
        end_dt = dt.datetime.combine(target_date, dt.time.max)

        # UPI Transactions
        txns = session.exec(
            select(Transaction).where(
                Transaction.merchant_id == merchant_id,
                Transaction.ts >= start_dt,
                Transaction.ts <= end_dt,
                Transaction.status == "SUCCESS"
            )
        ).all()
        upi_revenue = round(sum(t.amount for t in txns), 2)
        upi_count = len(txns)

        # Cash Log
        cash_record = session.exec(
            select(CashLog).where(
                CashLog.merchant_id == merchant_id,
                CashLog.date == target_date
            )
        ).first()
        cash_in = round(cash_record.cash_in, 2) if cash_record else 0.0

        # Expenses
        expenses = session.exec(
            select(Expense).where(
                Expense.merchant_id == merchant_id,
                Expense.date == target_date
            )
        ).all()
        total_expense = round(sum(e.amount for e in expenses), 2)
        expense_breakdown = [
            {"category": e.category, "amount": e.amount, "description": e.source_text}
            for e in expenses
        ]

        # Total revenue and true net profit
        total_revenue = round(upi_revenue + cash_in, 2)
        net_profit = round(total_revenue - total_expense, 2)
        margin_pct = round((net_profit / total_revenue * 100.0), 1) if total_revenue > 0 else 0.0

        return {
            "date": str(target_date),
            "upi_revenue": upi_revenue,
            "upi_count": upi_count,
            "cash_in": cash_in,
            "total_revenue": total_revenue,
            "total_expense": total_expense,
            "net_profit": net_profit,
            "margin_pct": margin_pct,
            "expense_breakdown": expense_breakdown
        }

    @staticmethod
    def get_revenue_trend(
        session: Session, 
        merchant_id: str, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Returns daily revenue trend for the last N days.
        """
        latest_txn = session.exec(
            select(Transaction).where(Transaction.merchant_id == merchant_id).order_by(Transaction.ts.desc())
        ).first()
        if not latest_txn:
            return []

        end_date = latest_txn.ts.date()
        start_date = end_date - dt.timedelta(days=days - 1)
        start_dt = dt.datetime.combine(start_date, dt.time.min)

        txns = session.exec(
            select(Transaction).where(
                Transaction.merchant_id == merchant_id,
                Transaction.ts >= start_dt,
                Transaction.status == "SUCCESS"
            )
        ).all()

        daily_data: Dict[dt.date, float] = {
            (start_date + dt.timedelta(days=i)): 0.0 for i in range(days)
        }
        for t in txns:
            t_date = t.ts.date()
            if t_date in daily_data:
                daily_data[t_date] += t.amount

        # Also add cash if available
        cash_logs = session.exec(
            select(CashLog).where(
                CashLog.merchant_id == merchant_id,
                CashLog.date >= start_date
            )
        ).all()
        daily_cash = {c.date: c.cash_in for c in cash_logs}

        trend = []
        for d, upi_val in sorted(daily_data.items()):
            c_val = daily_cash.get(d, 0.0)
            trend.append({
                "date": str(d),
                "day_name": d.strftime("%a"),
                "upi_revenue": round(upi_val, 2),
                "cash_revenue": round(c_val, 2),
                "total_revenue": round(upi_val + c_val, 2)
            })
        return trend

    @staticmethod
    def get_hourly_heatmap(
        session: Session, 
        merchant_id: str
    ) -> List[Dict[str, Any]]:
        """
        Computes average volume and revenue by day-of-week (0=Mon to 6=Sun) and hour (0-23).
        """
        txns = session.exec(
            select(Transaction).where(
                Transaction.merchant_id == merchant_id,
                Transaction.status == "SUCCESS"
            )
        ).all()

        # Matrix [day_of_week][hour]
        counts = np.zeros((7, 24), dtype=int)
        amounts = np.zeros((7, 24), dtype=float)

        for t in txns:
            w = t.ts.weekday()
            h = t.ts.hour
            counts[w][h] += 1
            amounts[w][h] += t.amount

        # Number of weeks in dataset (~ 38 weeks)
        num_weeks = 38.0
        avg_counts = (counts / num_weeks).round(1)

        result = []
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for w in range(7):
            for h in range(24):
                result.append({
                    "day_of_week": w,
                    "day_name": day_names[w],
                    "hour": h,
                    "avg_count": float(avg_counts[w][h]),
                    "total_revenue": round(float(amounts[w][h]), 2)
                })
        return result
