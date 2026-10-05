import datetime as dt
from typing import Dict, Any
from sqlmodel import Session, select
from app.core.database import engine
from app.services.metrics import MetricsService
from app.services.opportunities import OpportunityService
from app.services.voice import VoiceSynthesizer
from app.agent.guardrails import GuardrailService

class MorningBriefService:
    """
    Generates the proactive daily morning brief for merchants.
    Provides yesterday's revenue, top growth opportunity, and one key action item.
    """

    @classmethod
    def generate_brief(cls, merchant_id: str, current_date: dt.date = None) -> Dict[str, Any]:
        if current_date is None:
            current_date = dt.date(2026, 9, 19)

        yesterday = current_date - dt.timedelta(days=1)

        with Session(engine) as session:
            # 1. Yesterday's financial summary
            daily_summary = MetricsService.get_daily_summary(session, merchant_id, yesterday)
            total_rev = int(daily_summary["total_revenue"])
            net_prof = int(daily_summary["net_profit"])

            # 2. Top Opportunity
            opps = OpportunityService.detect_all_opportunities(session, merchant_id, current_date)
            top_opp = opps[0] if opps else {
                "title": "Sabhi parameters normal hain",
                "estimated_impact_min": 0,
                "estimated_impact_max": 0
            }

            # 3. Spoken Hinglish script
            spoken_script = (
                f"Suprabhat Sharma ji! Kal dukaan par ₹{total_rev} ki kamai hui aur shuddh munafa ₹{net_prof} raha. "
                f"Aaj ka mukhya mauka: {top_opp['title']}. Phone pe pura hisab dekhein."
            )

            # 4. Generate TTS audio file (cached)
            audio_path = VoiceSynthesizer.synthesize_sync(spoken_script)

            # 5. Output-only Soundbox Announcement
            # Notice ends with prompt to check phone app
            announcement_text = f"Suprabhat! Kal ki kamai ₹{total_rev}. Phone pe brief dekhein."
            GuardrailService.announce_to_soundbox(
                merchant_id=merchant_id,
                text=announcement_text,
                audio=audio_path
            )

            return {
                "merchant_id": merchant_id,
                "date": str(current_date),
                "yesterday_revenue": total_rev,
                "yesterday_profit": net_prof,
                "top_opportunity": top_opp["title"],
                "suggested_action": top_opp.get("description", "Stock check karein"),
                "spoken_script": spoken_script,
                "audio_path": audio_path,
                "simulated": True
            }
