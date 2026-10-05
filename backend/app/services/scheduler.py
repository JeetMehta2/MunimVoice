import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.morning_brief import MorningBriefService
from app.agent.guardrails import GuardrailService
from app.core.config import settings

logger = logging.getLogger(__name__)

# Shared in-memory state tracking if End-of-Day ritual modal should be open on phone
_APP_RITUAL_STATE = {
    "end_of_day_active": False,
    "last_ritual_call": None
}

def is_eod_ritual_active() -> bool:
    return _APP_RITUAL_STATE["end_of_day_active"]

def set_eod_ritual_active(active: bool):
    _APP_RITUAL_STATE["end_of_day_active"] = active

def daily_morning_brief_job():
    """Scheduled 8:00 AM job: triggers proactive morning audio brief."""
    try:
        MorningBriefService.generate_brief(settings.HERO_MERCHANT_ID)
        logger.info("Executed scheduled daily morning brief.")
    except Exception as e:
        logger.error(f"Error in morning brief job: {e}")

def end_of_day_cash_ritual_job():
    """
    Scheduled 9:30 PM job:
    Soundbox announces: 'Din ka hisaab karein? Phone kholiye.'
    Opens Bahi-Khata ritual in phone app view.
    """
    try:
        announcement = "Din ka hisaab karein? Phone kholiye."
        GuardrailService.announce_to_soundbox(
            merchant_id=settings.HERO_MERCHANT_ID,
            text=announcement
        )
        set_eod_ritual_active(True)
        logger.info("Executed scheduled end-of-day cash ritual prompt.")
    except Exception as e:
        logger.error(f"Error in end-of-day cash ritual job: {e}")

scheduler = BackgroundScheduler()

def start_scheduler():
    if not scheduler.running:
        # Schedule morning brief at 8:00 AM daily
        scheduler.add_job(
            daily_morning_brief_job,
            CronTrigger(hour=8, minute=0),
            id="morning_brief_job",
            replace_existing=True
        )
        # Schedule end-of-day cash ritual at 9:30 PM (21:30) daily
        scheduler.add_job(
            end_of_day_cash_ritual_job,
            CronTrigger(hour=21, minute=30),
            id="eod_cash_ritual_job",
            replace_existing=True
        )
        scheduler.start()
        logger.info("APScheduler initialized for Munim background rituals.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
