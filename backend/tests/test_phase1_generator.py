import pytest
from datetime import datetime, timedelta, date
from sqlmodel import Session, select
from app.core.database import engine
from app.models.entities import (
    Merchant,
    Customer,
    Transaction,
    UdhaarRecord,
    CashLog,
    Expense,
)
from app.sim.ground_truth_models import MenuItemTruth
from app.core.ground_truth_db import get_ground_truth_session

def test_merchants_seeded():
    with Session(engine) as session:
        merchants = session.exec(select(Merchant)).all()
        assert len(merchants) == 6
        merchant_ids = {m.id for m in merchants}
        assert "merchant_sharma_chai" in merchant_ids
        assert "merchant_gupta_kirana" in merchant_ids
        assert "merchant_annapurna_tiffin" in merchant_ids
        assert "merchant_star_salon" in merchant_ids
        assert "merchant_fresh_juice" in merchant_ids
        assert "merchant_golden_crust" in merchant_ids

def test_ground_truth_menu_exists():
    with get_ground_truth_session() as session:
        hero_menu = session.exec(
            select(MenuItemTruth).where(MenuItemTruth.merchant_id == "merchant_sharma_chai")
        ).all()
        assert len(hero_menu) >= 5
        item_names = {it.name: it.price for it in hero_menu}
        assert "Masala Chai" in item_names
        assert item_names["Masala Chai"] == 10.0
        assert "Kulhad Kesar Chai" in item_names
        assert item_names["Kulhad Kesar Chai"] == 40.0

def test_story1_dead_tuesday_afternoon():
    """
    Planted Story 1: Dead Tuesday 2 PM to 5 PM (14:00 to 17:00)
    Tuesday 14-17 volume should be significantly lower than other weekdays (e.g. Wed, Thu, Fri) 14-17.
    """
    with Session(engine) as session:
        txns = session.exec(
            select(Transaction).where(Transaction.merchant_id == "merchant_sharma_chai")
        ).all()
        
        tuesday_afternoon_count = 0
        wednesday_afternoon_count = 0
        thursday_afternoon_count = 0
        
        for t in txns:
            if 14 <= t.ts.hour < 17:
                if t.ts.weekday() == 1:  # Tuesday
                    tuesday_afternoon_count += 1
                elif t.ts.weekday() == 2:  # Wednesday
                    wednesday_afternoon_count += 1
                elif t.ts.weekday() == 3:  # Thursday
                    thursday_afternoon_count += 1
                    
        assert wednesday_afternoon_count > 0
        # Tuesday should have dropped by roughly 80-85%
        ratio = tuesday_afternoon_count / wednesday_afternoon_count
        assert ratio < 0.35, f"Tuesday ratio {ratio} was not significantly lower than Wednesday"

def test_story2_churned_customers():
    """
    Planted Story 2: Exactly 25 regular customers who stopped coming in the last 30 days.
    """
    with Session(engine) as session:
        # Latest transaction date
        latest_txn = session.exec(
            select(Transaction).where(Transaction.merchant_id == "merchant_sharma_chai").order_by(Transaction.ts.desc())
        ).first()
        cutoff_date = latest_txn.ts - timedelta(days=30)
        
        # Check hero churned customer IDs (cust_0010 to cust_0034)
        churned_ids = [f"merchant_sharma_chai_cust_{i:04d}" for i in range(10, 35)]
        assert len(churned_ids) == 25
        
        for cid in churned_ids:
            recent_txns = session.exec(
                select(Transaction).where(
                    Transaction.merchant_id == "merchant_sharma_chai",
                    Transaction.customer_id == cid,
                    Transaction.ts >= cutoff_date
                )
            ).all()
            assert len(recent_txns) == 0, f"Customer {cid} had transactions in last 30 days!"
            
            # Prior history should exist
            prior_txns = session.exec(
                select(Transaction).where(
                    Transaction.merchant_id == "merchant_sharma_chai",
                    Transaction.customer_id == cid,
                    Transaction.ts < cutoff_date
                )
            ).all()
            assert len(prior_txns) > 0, f"Customer {cid} had no prior transactions"

def test_story3_high_margin_evening_undersell():
    """
    Planted Story 3: High-margin Kulhad Kesar Chai (Rs 40) under-sells in the evening (17-21).
    """
    with Session(engine) as session:
        morning_40 = session.exec(
            select(Transaction).where(
                Transaction.merchant_id == "merchant_sharma_chai",
                Transaction.amount == 40.0
            )
        ).all()
        
        morning_count = sum(1 for t in morning_40 if 8 <= t.ts.hour < 12)
        evening_count = sum(1 for t in morning_40 if 17 <= t.ts.hour < 21)
        
        # Morning count should be significantly higher than evening count for Rs 40 item (>65% drop)
        assert morning_count > 50
        assert evening_count < morning_count * 0.35, f"Evening count {evening_count} vs morning {morning_count}"

def test_story4_weekend_rush():
    """
    Planted Story 4: Weekend rush at 5 to 8 PM (17:00 to 20:00).
    Weekend 17-20 volume should be higher than weekday 17-20 volume per day.
    """
    with Session(engine) as session:
        txns = session.exec(
            select(Transaction).where(Transaction.merchant_id == "merchant_sharma_chai")
        ).all()
        
        weekend_rush_txns = [t for t in txns if t.ts.weekday() in (5, 6) and 17 <= t.ts.hour < 20]
        weekday_evening_txns = [t for t in txns if t.ts.weekday() in (0, 1, 2, 3) and 17 <= t.ts.hour < 20]
        
        # Per-day average: weekends ~ 2 days/week (78 days), weekdays ~ 4 days/week (156 days)
        weekend_per_day = len(weekend_rush_txns) / 78.0
        weekday_per_day = len(weekday_evening_txns) / 156.0
        
        assert weekend_per_day > weekday_per_day * 1.15

def test_story5_settlement_delay_gap():
    """
    Planted Story 5: Delayed settlements (5-8 days lag) in month 7.
    """
    with Session(engine) as session:
        delayed_txns = session.exec(
            select(Transaction).where(
                Transaction.merchant_id == "merchant_sharma_chai",
                Transaction.settlement_delayed == True
            )
        ).all()
        assert len(delayed_txns) > 100
        # Verify delay is >= 3 days
        for dt in delayed_txns[:10]:
            diff_days = (dt.settlement_ts - dt.ts).total_seconds() / 86400.0
            assert diff_days >= 3.0

def test_story6_udhaar_borrowers():
    """
    Planted Story 6: 8 udhaar borrowers, 2 of them overdue 15+ days.
    """
    with Session(engine) as session:
        udhaars = session.exec(
            select(UdhaarRecord).where(UdhaarRecord.merchant_id == "merchant_sharma_chai")
        ).all()
        assert len(udhaars) == 8
        
        latest_date = date(2026, 9, 19)
        overdue_15_plus = [
            u for u in udhaars 
            if u.due_date and (latest_date - u.due_date).days >= 15 and u.status == "PENDING"
        ]
        assert len(overdue_15_plus) >= 2
