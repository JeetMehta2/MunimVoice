from typing import Optional
from sqlmodel import SQLModel, Field

class MenuItemTruth(SQLModel, table=True):
    """
    GROUND TRUTH ONLY.
    Stored in ground_truth.db, completely isolated from munim.db.
    Used exclusively by the simulator and evaluation harness.
    Inference code must never import this model.
    """
    __tablename__ = "menu_items_truth"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    merchant_id: str = Field(index=True)
    name: str
    price: float = Field(index=True)
    cost: float = Field(default=0.0)
    margin_pct: float = Field(default=0.5)
    category: str = Field(default="general")
    is_hero_item: bool = Field(default=False)
