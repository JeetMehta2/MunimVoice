import json
import datetime as dt
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON, String, Text

class Merchant(SQLModel, table=True):
    __tablename__ = "merchants"
    
    id: str = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    business_type: str = Field(index=True)  # chai, kirana, tiffin, salon, juice, bakery
    city: str = Field(default="Jaipur")
    phone: Optional[str] = None
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)

class Customer(SQLModel, table=True):
    __tablename__ = "customers"
    
    id: str = Field(default=None, primary_key=True)
    merchant_id: str = Field(index=True, foreign_key="merchants.id")
    anonymized_id: str = Field(index=True)  # cust_xxxx
    nickname: Optional[str] = None  # e.g. "Ramesh Auto", "Sharma Ji"
    total_visits: int = Field(default=0)
    total_spent: float = Field(default=0.0)
    first_seen: dt.datetime = Field(default_factory=dt.datetime.utcnow)
    last_seen: dt.datetime = Field(default_factory=dt.datetime.utcnow)
    is_regular: bool = Field(default=False)

class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"
    
    id: str = Field(default=None, primary_key=True)
    merchant_id: str = Field(index=True, foreign_key="merchants.id")
    customer_id: Optional[str] = Field(default=None, index=True)
    amount: float = Field(index=True)
    ts: dt.datetime = Field(index=True)  # timestamp of payment
    status: str = Field(default="SUCCESS")  # SUCCESS, FAILED
    settlement_ts: Optional[dt.datetime] = None  # timestamp when settled to merchant bank account
    settlement_delayed: bool = Field(default=False)  # planted story flag

class PricePointHypothesis(SQLModel, table=True):
    """
    Inferred item hypotheses per price point without reading ground truth.
    Candidate items rank with confidence, updatable by Bayesian merchant confirmation.
    """
    __tablename__ = "price_point_hypotheses"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    merchant_id: str = Field(index=True, foreign_key="merchants.id")
    amount: float = Field(index=True)
    candidate_items: str = Field(default="[]")  # JSON list of candidates e.g. [{"name": "Masala Chai", "confidence": 0.85, "composition": "1x Masala Chai"}]
    confidence: float = Field(default=0.5)
    confirmed_by_merchant: bool = Field(default=False)
    confirmed_item: Optional[str] = None
    updated_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)

    def get_candidates(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self.candidate_items)
        except Exception:
            return []

    def set_candidates(self, candidates: List[Dict[str, Any]]):
        self.candidate_items = json.dumps(candidates)

class CashLog(SQLModel, table=True):
    __tablename__ = "cash_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    merchant_id: str = Field(index=True, foreign_key="merchants.id")
    date: dt.date = Field(index=True)
    cash_in: float
    source_text: Optional[str] = None  # Voice transcript or manual note
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)

class Expense(SQLModel, table=True):
    __tablename__ = "expenses"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    merchant_id: str = Field(index=True, foreign_key="merchants.id")
    date: dt.date = Field(index=True)
    category: str = Field(index=True)  # milk, tea_leaves, gas, rent, groceries, packaging, misc
    amount: float
    source_text: Optional[str] = None
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)

class UdhaarRecord(SQLModel, table=True):
    __tablename__ = "udhaar_ledger"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    merchant_id: str = Field(index=True, foreign_key="merchants.id")
    customer_id: Optional[str] = None
    customer_name: str = Field(index=True)
    amount: float
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
    due_date: Optional[dt.date] = None
    status: str = Field(default="PENDING", index=True)  # PENDING, RECOVERED, WRITTEN_OFF
    reminder_history: str = Field(default="[]")  # JSON list of sent reminders

    def get_reminders(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self.reminder_history)
        except Exception:
            return []

    def add_reminder(self, reminder: Dict[str, Any]):
        rems = self.get_reminders()
        rems.append(reminder)
        self.reminder_history = json.dumps(rems)

class Opportunity(SQLModel, table=True):
    __tablename__ = "opportunities"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    merchant_id: str = Field(index=True, foreign_key="merchants.id")
    type: str = Field(index=True)  # slow_slot, churned_customers, underperforming_high_margin_item, settlement_delay_cashflow_gap, rush_stock_prep, udhaar_overdue
    title: str
    description: str
    window: Optional[str] = None  # e.g. "Tuesday 2 PM - 5 PM"
    estimated_impact_min: float = Field(default=0.0)
    estimated_impact_max: float = Field(default=0.0)
    confidence: float = Field(default=0.8)
    evidence: str = Field(default="{}")  # JSON object with supporting stats
    status: str = Field(default="OPEN", index=True)  # OPEN, PROPOSED, APPROVED, REJECTED, SUPPRESSED
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)

    def get_evidence(self) -> Dict[str, Any]:
        try:
            return json.loads(self.evidence)
        except Exception:
            return {}

class Campaign(SQLModel, table=True):
    __tablename__ = "campaigns"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    merchant_id: str = Field(index=True, foreign_key="merchants.id")
    opportunity_id: Optional[int] = Field(default=None, foreign_key="opportunities.id")
    name: str
    offer_text: str  # e.g. "Chai pe 20% chhoot Tuesday 2-5 PM"
    discount_pct: float = Field(default=0.0)
    audience_count: int = Field(default=0)
    status: str = Field(default="PENDING_APPROVAL", index=True)  # PENDING_APPROVAL, ACTIVE, COMPLETED, CANCELLED
    start_time: Optional[dt.datetime] = None
    end_time: Optional[dt.datetime] = None
    holdout_flag: bool = Field(default=True)  # 20% holdout group for simulated uplift
    holdout_pct: float = Field(default=0.20)
    simulated_uplift: str = Field(default="{}")  # JSON of uplift results
    budget: float = Field(default=500.0)
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)

    def get_uplift(self) -> Dict[str, Any]:
        try:
            return json.loads(self.simulated_uplift)
        except Exception:
            return {}

class Approval(SQLModel, table=True):
    __tablename__ = "approvals"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    merchant_id: str = Field(index=True, foreign_key="merchants.id")
    actor: str = Field(default="merchant")
    action: str  # e.g. "START_CAMPAIGN", "SEND_UDHAAR_REMINDER"
    risk_tier: int = Field(default=2)  # 0: Auto-read, 1: Auto-draft, 2: Explicit Approval
    payload: str = Field(default="{}")  # JSON of the planned action
    idempotency_key: str = Field(unique=True, index=True)
    status: str = Field(default="PENDING_APPROVAL", index=True)  # PENDING_APPROVAL, APPROVED, REJECTED
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
    resolved_at: Optional[dt.datetime] = None

class AuditLogEntry(SQLModel, table=True):
    __tablename__ = "audit_log"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    merchant_id: str = Field(index=True, foreign_key="merchants.id")
    actor: str
    action: str
    risk_tier: int
    payload: str = Field(default="{}")
    idempotency_key: Optional[str] = None
    ts: dt.datetime = Field(default_factory=dt.datetime.utcnow, index=True)

class ScoreSnapshot(SQLModel, table=True):
    __tablename__ = "score_snapshots"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    merchant_id: str = Field(index=True, foreign_key="merchants.id")
    date: dt.date = Field(index=True)
    score: float = Field(default=0.0)  # 0 to 100
    consistency_score: float = Field(default=0.0)  # 0-25
    growth_score: float = Field(default=0.0)       # 0-20
    repeat_score: float = Field(default=0.0)       # 0-20
    udhaar_score: float = Field(default=0.0)       # 0-20
    cash_score: float = Field(default=0.0)         # 0-15
    indicative_limit_min: float = Field(default=0.0)
    indicative_limit_max: float = Field(default=0.0)
    recommendation: str = Field(default="")
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)

class ConversationMessage(SQLModel, table=True):
    __tablename__ = "conversations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    merchant_id: str = Field(index=True, foreign_key="merchants.id")
    session_id: str = Field(index=True)
    role: str  # user, assistant, system, tool
    content: str
    tool_calls: Optional[str] = None  # JSON if any
    tool_results: Optional[str] = None  # JSON if any
    audio_url: Optional[str] = None
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
