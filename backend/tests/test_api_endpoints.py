import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.munim_score import SCORE_DISCLAIMER

client = TestClient(app)

def test_health_and_merchants_list():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "HEALTHY"

    merchants_res = client.get("/api/merchants")
    assert merchants_res.status_code == 200
    merchants = merchants_res.json()
    assert len(merchants) == 6
    assert any(m["id"] == "merchant_sharma_chai" for m in merchants)

def test_daily_summary_endpoint():
    res = client.get("/api/merchants/merchant_sharma_chai/summary")
    assert res.status_code == 200
    data = res.json()
    assert "upi_revenue" in data
    assert "cash_in" in data
    assert "net_profit" in data
    assert data["total_revenue"] == round(data["upi_revenue"] + data["cash_in"], 2)

def test_product_mix_and_confirmation():
    res = client.get("/api/merchants/merchant_sharma_chai/product-mix")
    assert res.status_code == 200
    mix = res.json()
    assert len(mix) > 0

    confirm_res = client.post(
        "/api/merchants/merchant_sharma_chai/confirm-item",
        json={"amount": 10.0, "confirmed_item": "Masala Chai"}
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "confirmed"

def test_burst_injection_endpoint():
    res = client.post(
        "/api/merchants/merchant_sharma_chai/inject-burst",
        json={"count": 16, "amount": 20.0}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["injected_count"] == 16
    assert data["analysis"]["status"] == "RUSH"

def test_voice_parser_endpoint():
    res = client.post(
        "/api/bahi-khata/parse-voice",
        json={"transcript": "Aaj cash teen hazaar do sau mila aur doodh ka paanch sau rupaye diya"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["cash_in"] == 3200.0
    assert data["total_expense"] == 500.0

def test_munim_score_endpoint():
    res = client.get("/api/merchants/merchant_sharma_chai/score")
    assert res.status_code == 200
    data = res.json()
    assert 0 <= data["score"] <= 100
    assert data["disclaimer"] == SCORE_DISCLAIMER
    assert data["simulated"] is True
    assert "consistency" in data["factors"]
    assert "growth" in data["factors"]

def test_eval_results_endpoint():
    res = client.get("/api/eval/results")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert data["summary"]["item_inference_f1"] >= 0.75
