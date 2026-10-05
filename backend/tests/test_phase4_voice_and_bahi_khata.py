import pytest
import datetime as dt
from sqlmodel import Session, select
from app.core.database import engine
from app.services.voice import HinglishVoiceParser
from app.services.udhaar import UdhaarService
from app.services.munim_score import MunimScoreService, SCORE_DISCLAIMER
from app.services.morning_brief import MorningBriefService

def test_hinglish_voice_parser_numbers_and_expenses():
    # 1. Hindi number words
    assert HinglishVoiceParser.parse_number_phrase("teen hazaar do sau") == 3200.0
    assert HinglishVoiceParser.parse_number_phrase("paanch sau") == 500.0
    assert HinglishVoiceParser.parse_number_phrase("bees hazaar") == 20000.0
    assert HinglishVoiceParser.parse_number_phrase("pachees sau") == 2500.0

    # 2. Combined Bahi-Khata speech
    text = "Aaj cash teen hazaar do sau mila aur doodh ka chheh sau rupaye diya"
    res = HinglishVoiceParser.extract_bahi_khata_fields(text)
    assert res["cash_in"] == 3200.0
    assert len(res["expenses"]) == 1
    assert res["expenses"][0]["category"] == "milk"
    assert res["expenses"][0]["amount"] == 600.0
    assert "Cash ₹3200, kharcha ₹600" in res["confirmation_message"]

def test_udhaar_service_ledger_and_tones():
    merchant_id = "merchant_sharma_chai"
    with Session(engine) as session:
        ledger = UdhaarService.get_ledger(session, merchant_id)
        assert len(ledger) == 8
        
        # Check critical overdue flag
        critical_items = [item for item in ledger if item["is_critical"]]
        assert len(critical_items) >= 2

        # Check reminder tone generation
        soft_msg = UdhaarService.draft_reminder_message("Ramesh", 650.0, "soft")
        firm_msg = UdhaarService.draft_reminder_message("Ramesh", 650.0, "firm")
        funny_msg = UdhaarService.draft_reminder_message("Ramesh", 650.0, "funny")

        assert "kushal mangal" in soft_msg
        assert "overdue ho chuka hai" in firm_msg
        assert "dosti barkarar" in funny_msg or "charcha" in funny_msg

        # Test Tier 2 reminder action creation
        action_res = UdhaarService.create_reminder_action(session, merchant_id, ledger[0]["id"], "firm")
        assert action_res["status"] == "PENDING_APPROVAL"
        assert action_res["risk_tier"] == 2

def test_munim_score_factors_and_disclaimer():
    merchant_id = "merchant_sharma_chai"
    with Session(engine) as session:
        score_data = MunimScoreService.evaluate_merchant_score(session, merchant_id)
        assert 0 <= score_data["score"] <= 100
        assert score_data["disclaimer"] == SCORE_DISCLAIMER
        assert score_data["simulated"] is True
        assert "consistency" in score_data["factors"]
        assert "growth" in score_data["factors"]
        assert "repeat_rate" in score_data["factors"]
        assert "udhaar_recovery" in score_data["factors"]
        assert "cash_discipline" in score_data["factors"]
        assert len(score_data["indicative_limit_band"]) > 0

def test_morning_brief_generation():
    merchant_id = "merchant_sharma_chai"
    brief = MorningBriefService.generate_brief(merchant_id, dt.date(2026, 9, 19))
    assert brief["yesterday_revenue"] > 0
    assert len(brief["top_opportunity"]) > 0
    assert "Suprabhat" in brief["spoken_script"]
    assert brief["simulated"] is True
