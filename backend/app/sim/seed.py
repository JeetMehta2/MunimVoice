import sys
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlmodel import SQLModel, Session
from app.core.database import engine, init_db
from app.core.ground_truth_db import ground_truth_engine, init_ground_truth_db
from app.sim.generator import generate_synthetic_data

def run_seed():
    print("Initializing database tables...")
    SQLModel.metadata.drop_all(engine)
    init_db()
    
    # Ground truth DB
    SQLModel.metadata.drop_all(ground_truth_engine)
    init_ground_truth_db()
    
    print("Generating 9 months of synthetic merchant data with planted stories...")
    with Session(engine) as session:
        stats = generate_synthetic_data(session)
        print(f"Seed complete!")
        print(f"  Merchants: {stats['merchants_seeded']}")
        print(f"  Total Transactions: {stats['transactions_generated']}")
        print(f"  Hero Udhaar Records: {stats['hero_udhaar_seeded']}")
        print(f"  Days Simulated: {stats['days_simulated']}")

if __name__ == "__main__":
    run_seed()
