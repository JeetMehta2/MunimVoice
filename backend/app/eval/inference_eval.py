from typing import Dict, Any, List
from collections import Counter
import numpy as np
from sqlmodel import Session, select
from app.models.entities import Merchant
from app.sim.ground_truth_models import MenuItemTruth
from app.core.ground_truth_db import get_ground_truth_session
from app.services.item_inference import ItemInferenceService, BUSINESS_DOMAIN_PRIORS

def evaluate_inference_accuracy(session: Session) -> Dict[str, Any]:
    """
    Evaluation harness that compares recovered product mix against hidden ground truth
    across seeded merchants (clean / easy baseline).
    """
    merchants = session.exec(select(Merchant)).all()
    results_by_merchant: Dict[str, Any] = {}

    total_gt_items = 0
    total_inferred_items = 0
    total_matches = 0
    total_top1_matches = 0

    with get_ground_truth_session() as gt_session:
        for m in merchants:
            gt_items = gt_session.exec(
                select(MenuItemTruth).where(MenuItemTruth.merchant_id == m.id)
            ).all()
            if not gt_items:
                continue
            gt_price_map = {round(item.price, 1): item.name.lower() for item in gt_items}

            inferred = ItemInferenceService.infer_product_mix(session, m.id)

            m_matches = 0
            m_top1_matches = 0
            inferred_base_prices = []

            for inf in inferred:
                amt = round(inf["amount"], 1)
                candidates = inf.get("candidates", [])
                candidate_names = [c["name"].lower() for c in candidates]

                if amt in gt_price_map:
                    inferred_base_prices.append(amt)
                    gt_name = gt_price_map[amt]
                    matched = any(gt_name in c_name or c_name in gt_name for c_name in candidate_names)
                    if matched:
                        m_matches += 1
                    
                    if candidates:
                        top1_name = candidates[0]["name"].lower()
                        if gt_name in top1_name or top1_name in gt_name:
                            m_top1_matches += 1

            precision = round(m_matches / max(1, len(inferred_base_prices)), 3)
            recall = round(m_matches / max(1, len(gt_items)), 3)
            f1 = round((2 * precision * recall) / max(1e-5, (precision + recall)), 3)
            top1_acc = round(m_top1_matches / max(1, len(gt_items)), 3)

            results_by_merchant[m.id] = {
                "merchant_name": m.name,
                "business_type": m.business_type,
                "ground_truth_count": len(gt_items),
                "inferred_count": len(inferred_base_prices),
                "matches": m_matches,
                "top1_matches": m_top1_matches,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "top1_accuracy": top1_acc
            }

            total_gt_items += len(gt_items)
            total_inferred_items += len(inferred_base_prices)
            total_matches += m_matches
            total_top1_matches += m_top1_matches

    overall_precision = round(total_matches / max(1, total_inferred_items), 3)
    overall_recall = round(total_matches / max(1, total_gt_items), 3)
    overall_f1 = round((2 * overall_precision * overall_recall) / max(1e-5, (overall_precision + overall_recall)), 3)
    overall_top1_acc = round(total_top1_matches / max(1, total_gt_items), 3)

    return {
        "overall_precision": overall_precision,
        "overall_recall": overall_recall,
        "overall_f1": overall_f1,
        "overall_top1_accuracy": overall_top1_acc,
        "target_met": (overall_f1 >= 0.75),
        "results_by_merchant": results_by_merchant
    }

def run_hard_case_stress_test(session: Session = None) -> Dict[str, Any]:
    """
    Adversarial stress test on synthetic data:
    - 7 ground truth items
    - 2 price collisions (Rs 10 Chai vs Biscuit, Rs 40 Kulhad Chai vs Cold Coffee)
    - 4 combo price combinations (Rs 30, 50, 60, 75)
    - 30 noise transactions
    - 1 sparse item (Bread Pakoda with only 2 transactions)
    """
    gt_menu = [
        {"name": "Masala Chai", "price": 10.0},
        {"name": "Biscuit Packet", "price": 10.0},
        {"name": "Samosa", "price": 20.0},
        {"name": "Bread Pakoda", "price": 25.0},
        {"name": "Special Bun Maska", "price": 35.0},
        {"name": "Kulhad Kesar Chai", "price": 40.0},
        {"name": "Cold Coffee", "price": 40.0}
    ]

    np.random.seed(42)
    txns = []
    for _ in range(120): txns.append(10.0)
    for _ in range(90): txns.append(20.0)
    for _ in range(2): txns.append(25.0)   # Sparse item: only 2 transactions
    for _ in range(60): txns.append(35.0)
    for _ in range(70): txns.append(40.0)

    # Combos
    for _ in range(45): txns.append(30.0)
    for _ in range(35): txns.append(50.0)
    for _ in range(25): txns.append(60.0)
    for _ in range(15): txns.append(75.0)

    # Noise
    noise_amounts = [13.0, 17.0, 27.0, 44.0, 63.0, 88.0]
    for _ in range(30):
        txns.append(float(np.random.choice(noise_amounts)))

    total_txns = len(txns)
    counts = Counter(txns)

    domain_priors = BUSINESS_DOMAIN_PRIORS["chai"]

    inferred_items = []
    for amt, freq in counts.most_common(20):
        if freq / total_txns < 0.02:
            continue
        candidates = []
        for item in domain_priors:
            if abs(item["typical_price"] - amt) == 0:
                candidates.append({"name": item["name"], "confidence": 0.88, "type": "single"})
        for b1 in domain_priors:
            p1 = b1["typical_price"]
            for b2 in domain_priors:
                p2 = b2["typical_price"]
                if b1["name"] < b2["name"] and p1 + p2 == amt:
                    candidates.append({"name": f"{b1['name']} + {b2['name']}", "confidence": 0.75, "type": "combo"})
        inferred_items.append({
            "amount": amt,
            "frequency": freq,
            "percentage": (freq / total_txns) * 100.0,
            "candidates": candidates
        })

    recalled_gt = 0
    top1_recalled_gt = 0

    for gt in gt_menu:
        gt_name = gt["name"].lower()
        gt_price = gt["price"]
        inf_cluster = next((c for c in inferred_items if abs(c["amount"] - gt_price) < 0.1), None)
        if inf_cluster and inf_cluster["candidates"]:
            cand_names = [c["name"].lower() for c in inf_cluster["candidates"]]
            if any(gt_name in cn or cn in gt_name for cn in cand_names):
                recalled_gt += 1
            if gt_name in cand_names[0] or cand_names[0] in gt_name:
                top1_recalled_gt += 1

    single_gt_prices = {gt["price"] for gt in gt_menu}
    valid_inferred_clusters = sum(1 for inf in inferred_items if inf["amount"] in single_gt_prices)

    precision = round(valid_inferred_clusters / max(1, len(inferred_items)), 3)
    recall = round(recalled_gt / len(gt_menu), 3)
    f1 = round((2 * precision * recall) / max(1e-5, (precision + recall)), 3)
    top1_acc = round(top1_recalled_gt / len(gt_menu), 3)

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "top1_accuracy": top1_acc,
        "ground_truth_count": len(gt_menu),
        "inferred_clusters_count": len(inferred_items),
        "recalled_items": recalled_gt,
        "top1_matches": top1_recalled_gt,
        "details": {
            "price_collisions": "Rs 10 (Chai/Biscuit), Rs 40 (Kulhad/Coffee)",
            "combos_present": ["10+20=30", "10+40=50", "20+40=60", "35+40=75"],
            "noise_transactions_count": 30,
            "missing_item": "Bread Pakoda (Rs 25, only 2 transactions, below 2% threshold)"
        }
    }
