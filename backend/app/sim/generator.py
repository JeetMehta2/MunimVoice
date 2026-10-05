import random
import json
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Any, Tuple
import numpy as np
from sqlmodel import Session

from app.models.entities import (
    Merchant,
    Customer,
    Transaction,
    UdhaarRecord,
    CashLog,
    Expense,
    PricePointHypothesis,
    ScoreSnapshot
)
from app.sim.ground_truth_models import MenuItemTruth
from app.core.ground_truth_db import get_ground_truth_session, init_ground_truth_db

# Deterministic Seed for Reproducibility
RANDOM_SEED = 42

MERCHANT_PROFILES = [
    {
        "id": "merchant_sharma_chai",
        "name": "Sharma Chai & Snacks",
        "business_type": "chai",
        "city": "Jaipur",
        "menu": [
            {"name": "Masala Chai", "price": 10.0, "cost": 3.0, "margin_pct": 0.70, "category": "tea"},
            {"name": "Ginger Adrak Chai", "price": 15.0, "cost": 4.5, "margin_pct": 0.70, "category": "tea"},
            {"name": "Samosa", "price": 20.0, "cost": 7.0, "margin_pct": 0.65, "category": "snacks"},
            {"name": "Bread Pakoda", "price": 25.0, "cost": 9.0, "margin_pct": 0.64, "category": "snacks"},
            {"name": "Kulhad Kesar Chai", "price": 40.0, "cost": 10.0, "margin_pct": 0.75, "category": "tea", "is_hero_item": True},
            {"name": "Special Bun Maska", "price": 35.0, "cost": 12.0, "margin_pct": 0.66, "category": "snacks"},
        ]
    },
    {
        "id": "merchant_gupta_kirana",
        "name": "Gupta Daily Needs",
        "business_type": "kirana",
        "city": "Delhi",
        "menu": [
            {"name": "Milk Pouch", "price": 32.0, "cost": 29.0, "margin_pct": 0.09, "category": "dairy"},
            {"name": "Brown Bread", "price": 40.0, "cost": 32.0, "margin_pct": 0.20, "category": "bakery"},
            {"name": "Sugar 1kg", "price": 48.0, "cost": 42.0, "margin_pct": 0.12, "category": "staples"},
            {"name": "Atta 5kg", "price": 210.0, "cost": 185.0, "margin_pct": 0.12, "category": "staples"},
            {"name": "Biscuits", "price": 20.0, "cost": 16.0, "margin_pct": 0.20, "category": "snacks"},
        ]
    },
    {
        "id": "merchant_annapurna_tiffin",
        "name": "Annapurna Tiffin Service",
        "business_type": "tiffin",
        "city": "Indore",
        "menu": [
            {"name": "Standard Thali", "price": 80.0, "cost": 42.0, "margin_pct": 0.475, "category": "meals"},
            {"name": "Special Thali", "price": 120.0, "cost": 55.0, "margin_pct": 0.54, "category": "meals"},
            {"name": "Gulab Jamun Pair", "price": 40.0, "cost": 15.0, "margin_pct": 0.625, "category": "dessert"},
        ]
    },
    {
        "id": "merchant_star_salon",
        "name": "Star Men's Grooming Salon",
        "business_type": "salon",
        "city": "Lucknow",
        "menu": [
            {"name": "Haircut", "price": 100.0, "cost": 10.0, "margin_pct": 0.90, "category": "hair"},
            {"name": "Shave", "price": 50.0, "cost": 5.0, "margin_pct": 0.90, "category": "shave"},
            {"name": "Head Massage", "price": 150.0, "cost": 15.0, "margin_pct": 0.90, "category": "massage"},
            {"name": "Facial Cleansing", "price": 300.0, "cost": 50.0, "margin_pct": 0.83, "category": "skin"},
        ]
    },
    {
        "id": "merchant_fresh_juice",
        "name": "Fresh Squeeze Corner",
        "business_type": "juice",
        "city": "Mumbai",
        "menu": [
            {"name": "Mosambi Juice", "price": 50.0, "cost": 20.0, "margin_pct": 0.60, "category": "citrus"},
            {"name": "Orange Juice", "price": 60.0, "cost": 24.0, "margin_pct": 0.60, "category": "citrus"},
            {"name": "Mango Shake", "price": 70.0, "cost": 28.0, "margin_pct": 0.60, "category": "seasonal"},
            {"name": "Fruit Bowl", "price": 80.0, "cost": 30.0, "margin_pct": 0.625, "category": "raw"},
        ]
    },
    {
        "id": "merchant_golden_crust",
        "name": "Golden Crust Bakery",
        "business_type": "bakery",
        "city": "Bengaluru",
        "menu": [
            {"name": "Veg Puff", "price": 25.0, "cost": 9.0, "margin_pct": 0.64, "category": "savoury"},
            {"name": "Egg Puff", "price": 30.0, "cost": 12.0, "margin_pct": 0.60, "category": "savoury"},
            {"name": "Pastry Slice", "price": 65.0, "cost": 22.0, "margin_pct": 0.66, "category": "cake"},
            {"name": "Plum Cake Loaf", "price": 120.0, "cost": 45.0, "margin_pct": 0.625, "category": "dry_cake"},
        ]
    }
]

# Planted Udhaar records for Hero Merchant
HERO_UDHAAR_PLANTS = [
    {"name": "Ramesh Kumar (Electrician)", "amount": 650.0, "days_ago": 28, "due_days_ago": 18, "status": "PENDING"}, # OVERDUE > 15d
    {"name": "Vikram Singh (Auto Driver)", "amount": 820.0, "days_ago": 25, "due_days_ago": 16, "status": "PENDING"}, # OVERDUE > 15d
    {"name": "Anil Sharma (Tailor)", "amount": 340.0, "days_ago": 12, "due_days_ago": 4, "status": "PENDING"},
    {"name": "Sunil Verma (Broker)", "amount": 180.0, "days_ago": 9, "due_days_ago": 2, "status": "PENDING"},
    {"name": "Pooja Devi (Teacher)", "amount": 250.0, "days_ago": 6, "due_days_ago": -2, "status": "PENDING"},
    {"name": "Gaurav Joshi (Medical)", "amount": 420.0, "days_ago": 5, "due_days_ago": -4, "status": "PENDING"},
    {"name": "Deepak Tailor", "amount": 150.0, "days_ago": 4, "due_days_ago": -5, "status": "PENDING"},
    {"name": "Mukesh Kirana Staff", "amount": 210.0, "days_ago": 2, "due_days_ago": -7, "status": "PENDING"},
]

def generate_synthetic_data(session: Session, end_date: datetime = None, days: int = 270):
    """
    Generates 9 months of synthetic data for 6 merchants with reproducible planted stories.
    """
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    
    if end_date is None:
        # Default fixed end date for reproducibility
        end_date = datetime(2026, 9, 19, 21, 0, 0)
    
    start_date = end_date - timedelta(days=days)
    
    # Pre-identified festival dates (relative to start_date)
    # Diwali ~ Day 150, Holi ~ Day 230
    festival_days = {150: "Diwali", 230: "Holi", 85: "Independence Day"}
    cricket_match_days = {195: "Ind vs Pak T20", 245: "IPL Final"}
    heavy_rain_days = set(range(110, 115))  # 5-day monsoon dip
    
    # 1. Create Merchants & Truth Menus
    init_ground_truth_db()
    with get_ground_truth_session() as gt_session:
        for profile in MERCHANT_PROFILES:
            merchant = Merchant(
                id=profile["id"],
                name=profile["name"],
                business_type=profile["business_type"],
                city=profile["city"],
                phone="+919876543210",
                created_at=start_date
            )
            session.add(merchant)
            
            for item in profile["menu"]:
                m_item = MenuItemTruth(
                    merchant_id=profile["id"],
                    name=item["name"],
                    price=item["price"],
                    cost=item["cost"],
                    margin_pct=item["margin_pct"],
                    category=item["category"],
                    is_hero_item=item.get("is_hero_item", False)
                )
                gt_session.add(m_item)
        gt_session.commit()
    session.commit()
    
    # 2. Generate Customers per Merchant
    hero_id = "merchant_sharma_chai"
    customers_by_merchant: Dict[str, List[Customer]] = {}
    
    for profile in MERCHANT_PROFILES:
        m_id = profile["id"]
        n_customers = 180 if m_id == hero_id else 100
        cust_list = []
        for c_idx in range(n_customers):
            nickname = None
            if m_id == hero_id and c_idx < 30:
                sample_nicks = [
                    "Ramesh Chai Regular", "Verma Ji BSNL", "Sharma Dairy", "Gupta Lawyer",
                    "Pappu Driver", "Sunil Postman", "Kishan Peon", "Bunty College",
                    "Doctor Sahab", "Pintu Delivery", "Kapil Press", "Dinesh Mechanic"
                ]
                nickname = sample_nicks[c_idx % len(sample_nicks)]
            
            c = Customer(
                id=f"{m_id}_cust_{c_idx:04d}",
                merchant_id=m_id,
                anonymized_id=f"cust_{m_id[:3]}_{c_idx:04d}",
                nickname=nickname,
                total_visits=0,
                total_spent=0.0,
                first_seen=start_date + timedelta(days=random.randint(0, 30)),
                last_seen=start_date,
                is_regular=(c_idx < 40)
            )
            session.add(c)
            cust_list.append(c)
        customers_by_merchant[m_id] = cust_list
    session.commit()
    
    # Planted Customer Story: Hero merchant has exactly 25 regular customers who stopped in last 30 days
    # (Customers 10 to 34 are regular customers whose visits cease strictly before (end_date - 30 days))
    hero_churned_cust_ids = set(f"{hero_id}_cust_{i:04d}" for i in range(10, 35))
    
    # 3. Simulate Daily Transactions across 270 Days
    all_transactions = []
    
    for day_offset in range(days):
        current_day = start_date + timedelta(days=day_offset)
        day_of_week = current_day.weekday() # 0 = Monday, 1 = Tuesday, ..., 5 = Saturday, 6 = Sunday
        is_weekend = day_of_week in (5, 6)
        is_tuesday = (day_of_week == 1)
        is_festival = day_offset in festival_days
        is_cricket = day_offset in cricket_match_days
        is_rainy = day_offset in heavy_rain_days
        
        # Delayed settlements planted in month 7 (days 180 to 210)
        settlement_delay_active = (180 <= day_offset <= 210)
        
        for profile in MERCHANT_PROFILES:
            m_id = profile["id"]
            menu = profile["menu"]
            customers = customers_by_merchant[m_id]
            is_hero = (m_id == hero_id)
            
            # Base number of transactions per day
            base_txns = 75 if is_hero else 40
            if is_festival:
                base_txns = int(base_txns * 2.2)
            elif is_rainy:
                base_txns = int(base_txns * 0.45)
            elif is_weekend:
                base_txns = int(base_txns * 1.35)
                
            # Simulate transactions throughout business hours (7:00 AM to 21:00 PM)
            num_txns_today = max(10, int(np.random.normal(base_txns, base_txns * 0.15)))
            
            for _ in range(num_txns_today):
                # Pick time of day based on realistic distribution
                # Morning peak: 8-11, Afternoon lull: 13-16, Evening rush: 17-20
                time_slot_rand = random.random()
                if time_slot_rand < 0.35:
                    hour = random.randint(7, 11)
                elif time_slot_rand < 0.60:
                    hour = random.randint(12, 16)
                else:
                    hour = random.randint(17, 21)
                
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                txn_dt = datetime.combine(current_day.date(), time(hour, minute, second))
                
                # --- Planted Story 1: Dead Tuesday 2 PM to 5 PM (14:00 to 17:00) ---
                if is_hero and is_tuesday and 14 <= hour < 17:
                    # Drop 85% of traffic in this slot
                    if random.random() > 0.15:
                        continue
                
                # --- Planted Story 4: Weekend Rush 5 PM to 8 PM (17:00 to 20:00) ---
                if is_hero and is_weekend and 17 <= hour < 20:
                    # Additional traffic burst
                    pass
                
                # Select Customer
                # Check churned customer restriction
                days_from_end = (end_date - txn_dt).days
                
                valid_customers = customers
                if is_hero and days_from_end <= 30:
                    valid_customers = [c for c in customers if c.id not in hero_churned_cust_ids]
                    
                selected_cust = random.choice(valid_customers) if valid_customers else None
                
                # Compose basket of 1 to 3 items
                # Planted Story 3: Kulhad Kesar Chai (price 40) under-sells in evening (17-21)
                basket_items = []
                num_items = random.choices([1, 2, 3], weights=[0.65, 0.28, 0.07])[0]
                
                for _ in range(num_items):
                    available_items = list(menu)
                    if is_hero and 17 <= hour < 21:
                        # Severely reduce probability of Kulhad Kesar Chai in evening
                        available_items = [it for it in menu if it["name"] != "Kulhad Kesar Chai"]
                        if random.random() < 0.03: # tiny chance
                            available_items.append(next(it for it in menu if it["name"] == "Kulhad Kesar Chai"))
                    
                    chosen = random.choice(available_items)
                    basket_items.append(chosen)
                
                total_amount = sum(it["price"] for it in basket_items)
                
                # Settlement timing
                settlement_delay_days = 1
                if is_hero and settlement_delay_active:
                    # Planted Story 5: Delayed settlements (5-8 days lag)
                    settlement_delay_days = random.randint(5, 8)
                settlement_dt = txn_dt + timedelta(days=settlement_delay_days, hours=random.randint(2, 6))
                
                txn_id = f"txn_{m_id[:3]}_{len(all_transactions):07d}"
                txn = Transaction(
                    id=txn_id,
                    merchant_id=m_id,
                    customer_id=selected_cust.id if selected_cust else None,
                    amount=total_amount,
                    ts=txn_dt,
                    status="SUCCESS",
                    settlement_ts=settlement_dt,
                    settlement_delayed=(settlement_delay_days > 2)
                )
                all_transactions.append(txn)
                
                if selected_cust:
                    selected_cust.total_visits += 1
                    selected_cust.total_spent += total_amount
                    if txn_dt > selected_cust.last_seen:
                        selected_cust.last_seen = txn_dt

    # Batch insert transactions
    BATCH_SIZE = 2500
    for i in range(0, len(all_transactions), BATCH_SIZE):
        session.add_all(all_transactions[i:i + BATCH_SIZE])
    session.commit()
    
    # 4. Plant Udhaar Records for Hero Merchant (Story 6)
    for plant in HERO_UDHAAR_PLANTS:
        created_dt = end_date - timedelta(days=plant["days_ago"])
        due_dt = (end_date - timedelta(days=plant["due_days_ago"])).date()
        u = UdhaarRecord(
            merchant_id=hero_id,
            customer_name=plant["name"],
            amount=plant["amount"],
            created_at=created_dt,
            due_date=due_dt,
            status=plant["status"],
            reminder_history=json.dumps([])
        )
        session.add(u)
    session.commit()
    
    # 5. Plant Cash Logs & Expenses for Hero Merchant (last 30 days)
    for d in range(30):
        log_date = (end_date - timedelta(days=d)).date()
        # Daily cash ~ Rs 1500 - 3500
        cash_val = round(float(np.random.normal(2400, 400)), -1)
        c_log = CashLog(
            merchant_id=hero_id,
            date=log_date,
            cash_in=max(800.0, cash_val),
            source_text=f"Aaj cash {int(cash_val)} mila"
        )
        session.add(c_log)
        
        # 1-3 daily expenses (Milk, tea leaves, gas, snacks ingredients)
        daily_expenses = [
            ("milk", round(float(np.random.normal(650, 60)), -1), "Amul Taaza doodh 10 litre"),
            ("tea_leaves", round(float(np.random.normal(250, 30)), -1), "Wagh Bakri chai patti"),
            ("gas", 280.0 if d % 4 == 0 else 0.0, "Commercial cylinder refill share"),
            ("groceries", round(float(np.random.normal(300, 50)), -1), "Cheeni, adrak aur masale"),
        ]
        for cat, amt, desc in daily_expenses:
            if amt > 0:
                exp = Expense(
                    merchant_id=hero_id,
                    date=log_date,
                    category=cat,
                    amount=amt,
                    source_text=desc
                )
                session.add(exp)
    session.commit()
    
    # 6. Initialize Score Snapshot for Hero Merchant
    snapshot = ScoreSnapshot(
        merchant_id=hero_id,
        date=end_date.date(),
        score=78.0,
        consistency_score=21.0,
        growth_score=15.0,
        repeat_score=16.0,
        udhaar_score=13.0,
        cash_score=13.0,
        indicative_limit_min=65000.0,
        indicative_limit_max=85000.0,
        recommendation="Tuesday dead-slot me offer chalao aur 2 overdue udhaar recover karo score 85+ karne ke liye.",
        created_at=end_date
    )
    session.add(snapshot)
    session.commit()
    
    return {
        "merchants_seeded": len(MERCHANT_PROFILES),
        "transactions_generated": len(all_transactions),
        "hero_udhaar_seeded": len(HERO_UDHAAR_PLANTS),
        "days_simulated": days,
    }

class CustomerResponseSimulator:
    """
    Simulates customer response to campaigns based on past visit behavior, discount, and timing.
    Used STRICTLY for counterfactual uplift measurement.
    """
    @staticmethod
    def predict_redemption(
        customer_visits: int,
        days_since_last_visit: int,
        discount_pct: float,
        is_target_window: bool
    ) -> Tuple[bool, float]:
        """
        Returns (redeemed: bool, redemption_probability: float)
        """
        # Base probability depends on discount
        base_p = min(0.60, max(0.02, discount_pct / 100.0 * 1.5))
        
        # Active regular customers respond better
        if customer_visits > 15:
            base_p *= 1.4
        elif customer_visits > 5:
            base_p *= 1.15
            
        # Lapsed customers respond with moderate probability if discount is good
        if days_since_last_visit > 20:
            if discount_pct >= 20.0:
                base_p *= 1.2
            else:
                base_p *= 0.6
                
        # Timing relevance
        if is_target_window:
            base_p *= 1.3
        else:
            base_p *= 0.7
            
        final_p = min(0.85, max(0.01, base_p))
        redeemed = (random.random() < final_p)
        return redeemed, round(final_p, 3)
