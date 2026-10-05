from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session
from app.core.config import DATA_DIR

# Dedicated SQLite database strictly for ground truth
# Isolated from the main munim.db
GROUND_TRUTH_DB_PATH = DATA_DIR / "ground_truth.db"
ground_truth_engine = create_engine(
    f"sqlite:///{GROUND_TRUTH_DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False}
)

def init_ground_truth_db():
    SQLModel.metadata.create_all(ground_truth_engine)

def get_ground_truth_session() -> Session:
    """
    CRITICAL ACCESS RULE:
    Only the synthetic data generator and the eval harness may call this function.
    Inference code and agents must NEVER call this.
    """
    return Session(ground_truth_engine)
