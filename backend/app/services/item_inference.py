import json
import itertools
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sqlmodel import Session, select
from app.models.entities import Transaction, Merchant, PricePointHypothesis

# Generic domain knowledge priors by business type (Strictly independent of DB ground truth)
BUSINESS_DOMAIN_PRIORS: Dict[str, List[Dict[str, Any]]] = {
    "chai": [
        {"name": "Masala Chai", "typical_price": 10.0, "category": "tea"},
        {"name": "Ginger Adrak Chai", "typical_price": 15.0, "category": "tea"},
        {"name": "Samosa", "typical_price": 20.0, "category": "snacks"},
        {"name": "Bread Pakoda", "typical_price": 25.0, "category": "snacks"},
        {"name": "Special Bun Maska", "typical_price": 35.0, "category": "snacks"},
        {"name": "Kulhad Kesar Chai", "typical_price": 40.0, "category": "tea"},
        {"name": "Biscuit Packet", "typical_price": 10.0, "category": "snacks"},
    ],
    "kirana": [
        {"name": "Biscuits", "typical_price": 20.0, "category": "snacks"},
        {"name": "Milk Pouch", "typical_price": 32.0, "category": "dairy"},
        {"name": "Brown Bread", "typical_price": 40.0, "category": "bakery"},
        {"name": "Sugar 1kg", "typical_price": 48.0, "category": "staples"},
        {"name": "Dal 1kg", "typical_price": 120.0, "category": "staples"},
        {"name": "Atta 5kg", "typical_price": 210.0, "category": "staples"},
    ],
    "tiffin": [
        {"name": "Gulab Jamun Pair", "typical_price": 40.0, "category": "dessert"},
        {"name": "Standard Thali", "typical_price": 80.0, "category": "meals"},
        {"name": "Special Thali", "typical_price": 120.0, "category": "meals"},
        {"name": "Sweet Box", "typical_price": 50.0, "category": "dessert"},
    ],
    "salon": [
        {"name": "Shave", "typical_price": 50.0, "category": "shave"},
        {"name": "Beard Trim", "typical_price": 80.0, "category": "shave"},
        {"name": "Haircut", "typical_price": 100.0, "category": "hair"},
        {"name": "Head Massage", "typical_price": 150.0, "category": "massage"},
        {"name": "Facial Cleansing", "typical_price": 300.0, "category": "skin"},
    ],
    "juice": [
        {"name": "Mosambi Juice", "typical_price": 50.0, "category": "citrus"},
        {"name": "Orange Juice", "typical_price": 60.0, "category": "citrus"},
        {"name": "Mango Shake", "typical_price": 70.0, "category": "seasonal"},
        {"name": "Fruit Bowl", "typical_price": 80.0, "category": "raw"},
    ],
    "bakery": [
        {"name": "Veg Puff", "typical_price": 25.0, "category": "savoury"},
        {"name": "Egg Puff", "typical_price": 30.0, "category": "savoury"},
        {"name": "Pastry Slice", "typical_price": 65.0, "category": "cake"},
        {"name": "Plum Cake Loaf", "typical_price": 120.0, "category": "dry_cake"},
    ]
}

class ItemInferenceService:
    """
    Infers product mix without POS data using frequency clustering,
    constrained combinatorial search, and Bayesian prior updates upon merchant confirmation.
    
    CRITICAL HONESTY RULE:
    This service NEVER reads or imports ground truth menu items or tables.
    """

    @classmethod
    def infer_product_mix(
        cls, 
        session: Session, 
        merchant_id: str
    ) -> List[Dict[str, Any]]:
        """
        Runs clustering and decomposition on merchant transactions to discover price points
        and candidate items. Persists or updates PricePointHypothesis table.
        """
        merchant = session.exec(select(Merchant).where(Merchant.id == merchant_id)).first()
        b_type = merchant.business_type if merchant else "chai"
        domain_priors = BUSINESS_DOMAIN_PRIORS.get(b_type, BUSINESS_DOMAIN_PRIORS["chai"])

        # 1. Fetch transaction distribution
        txns = session.exec(
            select(Transaction.amount).where(
                Transaction.merchant_id == merchant_id,
                Transaction.status == "SUCCESS"
            )
        ).all()
        if not txns:
            return []

        counts = Counter(txns)
        total_txns = len(txns)
        sorted_amounts = [amt for amt, _ in counts.most_common(20)]

        # Fetch existing merchant confirmations
        existing_hypotheses = session.exec(
            select(PricePointHypothesis).where(PricePointHypothesis.merchant_id == merchant_id)
        ).all()
        confirmed_map = {h.amount: h for h in existing_hypotheses if h.confirmed_by_merchant}

        # 2. Identify Primary Base Price Points (modal clusters)
        # Modal price points are amounts that form distinct peaks in the distribution
        base_price_points = []
        for amt in sorted_amounts:
            freq = counts[amt] / total_txns
            # If an amount appears frequently (>2% of total transactions)
            if freq >= 0.02:
                base_price_points.append(amt)

        # 3. For each significant price point, generate candidates
        results = []
        for amt in sorted_amounts:
            freq = counts[amt]
            pct = round((freq / total_txns) * 100.0, 1)

            # Check if already confirmed by merchant
            if amt in confirmed_map:
                h = confirmed_map[amt]
                results.append({
                    "amount": amt,
                    "frequency": freq,
                    "percentage": pct,
                    "confirmed": True,
                    "confirmed_item": h.confirmed_item,
                    "confidence": 1.0,
                    "candidates": h.get_candidates(),
                    "status": "confirmed"
                })
                continue

            # Candidate Generation:
            candidates: List[Dict[str, Any]] = []

            # A. Check single item matches from domain priors
            for item in domain_priors:
                diff = abs(item["typical_price"] - amt)
                if diff == 0:
                    candidates.append({
                        "name": item["name"],
                        "confidence": 0.88,
                        "composition": f"1x {item['name']}",
                        "category": item["category"]
                    })
                elif diff <= 2.0:
                    candidates.append({
                        "name": item["name"],
                        "confidence": 0.65,
                        "composition": f"1x {item['name']} (approx)",
                        "category": item["category"]
                    })

            # B. Constrained Combinatorial Decomposition:
            # Check sums of 2 to 3 base price items (e.g. 10+20=30, 2x15=30, etc.)
            for base_item in domain_priors:
                p1 = base_item["typical_price"]
                # 2x same item
                if p1 * 2 == amt:
                    candidates.append({
                        "name": f"2x {base_item['name']}",
                        "confidence": 0.78,
                        "composition": f"2x {base_item['name']}",
                        "category": base_item["category"]
                    })
                # 3x same item
                if p1 * 3 == amt:
                    candidates.append({
                        "name": f"3x {base_item['name']}",
                        "confidence": 0.70,
                        "composition": f"3x {base_item['name']}",
                        "category": base_item["category"]
                    })

                # Pair with another item
                for second_item in domain_priors:
                    p2 = second_item["typical_price"]
                    if base_item["name"] < second_item["name"]:
                        if p1 + p2 == amt:
                            candidates.append({
                                "name": f"{base_item['name']} + {second_item['name']}",
                                "confidence": 0.75,
                                "composition": f"1x {base_item['name']} + 1x {second_item['name']}",
                                "category": "combo"
                            })

            # Sort candidates by confidence
            candidates.sort(key=lambda x: x["confidence"], reverse=True)
            top_confidence = candidates[0]["confidence"] if candidates else 0.40

            # Default generic hypothesis if no domain prior matched
            if not candidates:
                candidates.append({
                    "name": f"Custom Item / Combo (₹{int(amt)})",
                    "confidence": 0.40,
                    "composition": f"Item priced at ₹{int(amt)}",
                    "category": "other"
                })

            item_info = {
                "amount": amt,
                "frequency": freq,
                "percentage": pct,
                "confirmed": False,
                "confirmed_item": None,
                "confidence": round(top_confidence, 2),
                "candidates": candidates[:4],
                "status": "inferred"
            }
            results.append(item_info)

            # Persist or update hypothesis in DB
            db_h = session.exec(
                select(PricePointHypothesis).where(
                    PricePointHypothesis.merchant_id == merchant_id,
                    PricePointHypothesis.amount == amt
                )
            ).first()
            if not db_h:
                db_h = PricePointHypothesis(
                    merchant_id=merchant_id,
                    amount=amt,
                    confidence=round(top_confidence, 2)
                )
                db_h.set_candidates(candidates[:4])
                session.add(db_h)
            else:
                if not db_h.confirmed_by_merchant:
                    db_h.confidence = round(top_confidence, 2)
                    db_h.set_candidates(candidates[:4])
                    session.add(db_h)

        session.commit()
        return results

    @classmethod
    def confirm_price_point(
        cls, 
        session: Session, 
        merchant_id: str, 
        amount: float, 
        confirmed_item_name: str
    ) -> Dict[str, Any]:
        """
        Bayesian-style update of priors when merchant confirms an item by voice or tap.
        E.g. Merchant says "₹20 = Samosa, sahi hai" -> updates model prior to 1.0.
        """
        hypothesis = session.exec(
            select(PricePointHypothesis).where(
                PricePointHypothesis.merchant_id == merchant_id,
                PricePointHypothesis.amount == amount
            )
        ).first()

        if not hypothesis:
            hypothesis = PricePointHypothesis(
                merchant_id=merchant_id,
                amount=amount
            )

        hypothesis.confirmed_by_merchant = True
        hypothesis.confirmed_item = confirmed_item_name
        hypothesis.confidence = 1.0

        # Update candidates list with confirmed item at top with 1.0 confidence
        candidates = hypothesis.get_candidates()
        updated_candidates = [
            {"name": confirmed_item_name, "confidence": 1.0, "composition": f"1x {confirmed_item_name}", "category": "confirmed"}
        ]
        for c in candidates:
            if c.get("name") != confirmed_item_name:
                updated_candidates.append(c)
        hypothesis.set_candidates(updated_candidates[:4])

        session.add(hypothesis)
        session.commit()

        return {
            "amount": amount,
            "confirmed_item": confirmed_item_name,
            "status": "confirmed",
            "message": f"Updated prior: ₹{int(amount)} confirmed as '{confirmed_item_name}'."
        }
