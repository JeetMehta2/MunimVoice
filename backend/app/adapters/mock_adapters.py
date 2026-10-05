import json
import uuid
import datetime as dt
from typing import Dict, Any, List, Optional
from sqlmodel import Session
from app.models.entities import AuditLogEntry

# Internal private token known ONLY to GuardrailService
_INTERNAL_GUARDRAIL_TOKEN = uuid.uuid4().hex

def get_guardrail_token_for_executor() -> str:
    """Only GuardrailService may import and invoke this to authorize external calls."""
    return _INTERNAL_GUARDRAIL_TOKEN


class MockSoundboxAdapter:
    """
    OUTPUT-ONLY Mock adapter for physical Paytm Soundbox device.
    Strictly Output-Only: Exposes ONLY announce(merchant_id, text, audio).
    NO listen, receive, reply, or mic methods exist.
    Direct calls without guardrail authorization token raise PermissionError.
    """
    _broadcast_history: List[Dict[str, Any]] = []

    @classmethod
    def announce(
        cls, 
        merchant_id: str, 
        text: str, 
        audio: Optional[str] = None, 
        *, 
        _auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        if _auth_token != _INTERNAL_GUARDRAIL_TOKEN:
            raise PermissionError(
                "Direct adapter call prohibited. Soundbox announce must be routed through GuardrailService with approval verification."
            )

        entry = {
            "id": f"sb_{uuid.uuid4().hex[:8]}",
            "merchant_id": merchant_id,
            "text": text,
            "audio": audio,
            "simulated": True,
            "timestamp": dt.datetime.utcnow().isoformat()
        }
        cls._broadcast_history.append(entry)
        return entry

    @classmethod
    def get_history(cls, merchant_id: str) -> List[Dict[str, Any]]:
        """Read-only view for UI logs."""
        return [e for e in cls._broadcast_history if e["merchant_id"] == merchant_id]


class MockUPICollectAdapter:
    """
    Mock adapter for sending UPI-collect payment requests.
    Direct calls without guardrail authorization token raise PermissionError.
    """
    _sent_collect_requests: List[Dict[str, Any]] = []

    @classmethod
    def send_collect_request(
        cls, 
        merchant_id: str, 
        customer_name: str, 
        amount: float, 
        message: str,
        *,
        _auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        if _auth_token != _INTERNAL_GUARDRAIL_TOKEN:
            raise PermissionError(
                "Direct adapter call prohibited. UPI Collect must be routed through GuardrailService with approval verification."
            )

        entry = {
            "id": f"upi_{uuid.uuid4().hex[:8]}",
            "merchant_id": merchant_id,
            "customer_name": customer_name,
            "amount": amount,
            "message": message,
            "simulated": True,
            "status": "SENT_SIMULATED",
            "timestamp": dt.datetime.utcnow().isoformat()
        }
        cls._sent_collect_requests.append(entry)
        return entry

    @classmethod
    def get_sent(cls, merchant_id: str) -> List[Dict[str, Any]]:
        return [e for e in cls._sent_collect_requests if e["merchant_id"] == merchant_id]


class MockMessagingAdapter:
    """
    Mock adapter for customer campaign outreach (WhatsApp / SMS).
    Direct calls without guardrail authorization token raise PermissionError.
    """
    _sent_messages: List[Dict[str, Any]] = []

    @classmethod
    def send_campaign_offer(
        cls, 
        merchant_id: str, 
        campaign_name: str, 
        recipient_count: int, 
        offer_text: str,
        *,
        _auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        if _auth_token != _INTERNAL_GUARDRAIL_TOKEN:
            raise PermissionError(
                "Direct adapter call prohibited. Customer messaging must be routed through GuardrailService with approval verification."
            )

        entry = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "merchant_id": merchant_id,
            "campaign_name": campaign_name,
            "recipient_count": recipient_count,
            "offer_text": offer_text,
            "simulated": True,
            "status": "DISPATCHED_SIMULATED",
            "timestamp": dt.datetime.utcnow().isoformat()
        }
        cls._sent_messages.append(entry)
        return entry

    @classmethod
    def get_sent(cls, merchant_id: str) -> List[Dict[str, Any]]:
        return [e for e in cls._sent_messages if e["merchant_id"] == merchant_id]


class AuditLogger:
    """
    Immutable audit log for all system and merchant actions.
    Records actor, action, tier, payload, idempotency key, timestamp.
    """
    @staticmethod
    def log(
        session: Session,
        merchant_id: str,
        actor: str,
        action: str,
        risk_tier: int,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            merchant_id=merchant_id,
            actor=actor,
            action=action,
            risk_tier=risk_tier,
            payload=json.dumps(payload),
            idempotency_key=idempotency_key or str(uuid.uuid4()),
            ts=dt.datetime.utcnow()
        )
        session.add(entry)
        session.commit()
        return entry
