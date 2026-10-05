import pytest
import datetime as dt
from sqlmodel import Session, select
from app.core.database import engine
from app.services.metrics import MetricsService
from app.services.item_inference import ItemInferenceService
from app.services.footfall import FootfallService
from app.services.opportunities import OpportunityService
from app.eval.inference_eval import evaluate_inference_accuracy

def test_metrics_service_daily_summary():
    with Session(engine) as session:
        summary = MetricsService.get_daily_summary(session, "merchant_sharma_chai")
        assert "upi_revenue" in summary
        assert "cash_in" in summary
        assert "total_expense" in summary
        assert "net_profit" in summary
        # True profit formula: UPI + Cash - Expense
        expected_profit = round(summary["upi_revenue"] + summary["cash_in"] - summary["total_expense"], 2)
        assert summary["net_profit"] == expected_profit

def test_item_inference_and_bayesian_update():
    with Session(engine) as session:
        # Run inference
        mix = ItemInferenceService.infer_product_mix(session, "merchant_sharma_chai")
        assert len(mix) > 0

        # Check that top modal prices (e.g. 10, 15, 20, 40) are present
        amounts = [m["amount"] for m in mix]
        assert 10.0 in amounts
        assert 20.0 in amounts

        # Check candidate items
        item_20 = next(m for m in mix if m["amount"] == 20.0)
        assert len(item_20["candidates"]) > 0
        candidate_names = [c["name"] for c in item_20["candidates"]]
        assert "Samosa" in candidate_names

        # Bayesian Update: Confirm ₹20 as Samosa
        res = ItemInferenceService.confirm_price_point(
            session, "merchant_sharma_chai", 20.0, "Samosa"
        )
        assert res["status"] == "confirmed"

        # Re-fetch inference and verify updated prior
        updated_mix = ItemInferenceService.infer_product_mix(session, "merchant_sharma_chai")
        updated_20 = next(m for m in updated_mix if m["amount"] == 20.0)
        assert updated_20["confirmed"] is True
        assert updated_20["confirmed_item"] == "Samosa"
        assert updated_20["confidence"] == 1.0

def test_inference_eval_harness_f1_score():
    with Session(engine) as session:
        eval_report = evaluate_inference_accuracy(session)
        print("\n=== Item Inference Evaluation Report ===")
        print(f"Overall Precision: {eval_report['overall_precision']}")
        print(f"Overall Recall:    {eval_report['overall_recall']}")
        print(f"Overall F1 Score:  {eval_report['overall_f1']}")
        print(f"Top-1 Accuracy:    {eval_report['overall_top1_accuracy']}")

        # Verify F1 score target
        assert eval_report["overall_f1"] >= 0.75, f"F1 Score {eval_report['overall_f1']} was below 0.75 target!"

def test_footfall_sensor_burst_triggers_rush():
    with Session(engine) as session:
        merchant_id = "merchant_sharma_chai"
        # Inject simulated burst of 15 payments in 5 minutes
        burst_result = FootfallService.inject_simulated_burst(
            session, merchant_id=merchant_id, count=16, amount=20.0
        )
        analysis = burst_result["analysis"]

        assert burst_result["injected_count"] == 16
        # Rush must be detected (Z-score > 2.0)
        assert analysis["z_score"] >= 2.0, f"Z-score {analysis['z_score']} did not exceed 2.0"
        assert analysis["status"] == "RUSH"
        assert "Rush aa raha hai" in analysis["announcement"]
        assert analysis["action_suggested"] == "prep_stock"

def test_opportunity_detectors():
    with Session(engine) as session:
        merchant_id = "merchant_sharma_chai"
        opps = OpportunityService.detect_all_opportunities(session, merchant_id)
        assert len(opps) >= 4

        opp_types = {o["type"] for o in opps}
        assert "slow_slot" in opp_types
        assert "churned_customers" in opp_types
        assert "underperforming_high_margin_item" in opp_types
        assert "udhaar_overdue" in opp_types

        # Verify each opportunity has estimated impact range and confidence
        for o in opps:
            assert o["estimated_impact_min"] >= 0
            assert o["estimated_impact_max"] >= o["estimated_impact_min"]
            assert 0.5 <= o["confidence"] <= 1.0
            assert len(o["evidence"]) > 0

def test_external_dip_suppression_dont_act():
    with Session(engine) as session:
        # Check monsoon rain date (Month 7, Day 12)
        rain_date = dt.date(2026, 7, 12)
        explanation = OpportunityService.explain_dip(session, "merchant_sharma_chai", rain_date)
        if explanation["is_dip"]:
            assert "DON'T ACT" in explanation["recommendation"]
            assert "Barish" in explanation["external_factor"]
