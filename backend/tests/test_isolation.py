import re
import pytest
from pathlib import Path
from sqlmodel import Session, select
from app.core.database import engine
from app.adapters.mock_adapters import (
    MockSoundboxAdapter, 
    MockUPICollectAdapter, 
    MockMessagingAdapter
)
from app.agent.guardrails import GuardrailService
from app.models.entities import Approval

def test_inference_code_does_not_import_or_query_ground_truth():
    """
    CHANGE 4: Ground-truth isolation test.
    Scans inference and agent modules to guarantee they never import MenuItemTruth
    or query the isolated ground truth session factory.
    """
    backend_app_dir = Path(__file__).resolve().parent.parent / "app"
    
    # Modules that must remain strictly blind to ground truth
    restricted_dirs = [
        backend_app_dir / "services" / "item_inference.py",
        backend_app_dir / "services" / "metrics.py",
        backend_app_dir / "services" / "opportunities.py",
        backend_app_dir / "agent" / "tools.py",
        backend_app_dir / "agent" / "executor.py",
    ]

    prohibited_patterns = [
        r"\bMenuItemTruth\b",
        r"\bmenu_items_truth\b",
        r"\bget_ground_truth_session\b",
        r"\bground_truth_engine\b",
        r"\bground_truth_db\b"
    ]

    for file_path in restricted_dirs:
        assert file_path.exists(), f"File {file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        
        for pattern in prohibited_patterns:
            matches = re.findall(pattern, content)
            assert len(matches) == 0, (
                f"Ground-Truth Isolation Violation! Found {pattern} in {file_path.name}: {matches}"
            )

def test_direct_adapter_call_without_token_raises_permission_error():
    """
    CHANGE 3: Proves that calling adapters directly without GuardrailService authorization fails.
    """
    # 1. Direct Soundbox announce attempt
    with pytest.raises(PermissionError) as exc_info:
        MockSoundboxAdapter.announce("merchant_sharma_chai", "Unchecked announcement")
    assert "Direct adapter call prohibited" in str(exc_info.value)

    # 2. Direct UPI collect attempt
    with pytest.raises(PermissionError) as exc_info:
        MockUPICollectAdapter.send_collect_request("merchant_sharma_chai", "Ramesh", 500.0, "Pay now")
    assert "Direct adapter call prohibited" in str(exc_info.value)

    # 3. Direct SMS / Messaging attempt
    with pytest.raises(PermissionError) as exc_info:
        MockMessagingAdapter.send_campaign_offer("merchant_sharma_chai", "Sale", 20, "20% off")
    assert "Direct adapter call prohibited" in str(exc_info.value)

def test_tier2_action_without_approval_never_executes():
    """
    CHANGE 3: Proves a Tier 2 action remains in PENDING_APPROVAL and never touches adapters
    until explicit approval is granted.
    """
    merchant_id = "merchant_sharma_chai"
    initial_sent_count = len(MockMessagingAdapter.get_sent(merchant_id))

    with Session(engine) as session:
        # Submit Tier 2 action
        res = GuardrailService.process_action(
            session=session,
            merchant_id=merchant_id,
            action_name="START_CAMPAIGN",
            risk_tier=2,
            payload={"campaign_name": "Unapproved Promo", "offer_text": "50% off", "budget": 300.0},
            idempotency_key="unapproved_campaign_test"
        )
        assert res["status"] == "PENDING_APPROVAL"

        # Check sent messages — must still be unchanged
        current_sent = len(MockMessagingAdapter.get_sent(merchant_id))
        assert current_sent == initial_sent_count, "Adapter was executed without approval!"
