import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
os.chdir(backend_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import Base, engine, SessionLocal
from app.services.seed_data import seed_database
from app.routers.demo import run_demonstration_scenario
from app.routers.marketplace import run_marketplace_demonstration_scenario

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ANN-DAAN AI Demonstration Scenarios Runner")
    parser.add_argument("--scenario", choices=["hostel", "marketplace", "all"], default="all",
                        help="Choose scenario to execute: hostel (Section 20), marketplace (Section 16), or all")
    args = parser.parse_args()

    # Ensure schema and seed data exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)

        if args.scenario in ["all", "marketplace"]:
            print("=" * 75)
            print("ANN-DAAN AI: Executing Section 16 Hybrid Commercial & Social Rescue Scenario")
            print("=" * 75)
            res_m = run_marketplace_demonstration_scenario(db)
            print("\n[SUCCESS] Section 16 Hybrid Scenario Completed:")
            print(f"  * Scenario: {res_m.get('scenario')}")
            print(f"  * Restaurant: {res_m.get('restaurant')}")
            print(f"  * Total Surplus Listed: {res_m.get('total_surplus_listed')} meals")
            print(f"  * Original Price: {res_m.get('original_price_per_meal')} -> AI Rescue Price: {res_m.get('ai_dynamic_rescue_price')}")
            print(f"  * Commercial Purchases: {res_m.get('commercial_sales')}")
            print(f"  * Rescue-to-Donation: {res_m.get('rescue_to_donation')}")
            print(f"  * Aggregate Impact: {res_m.get('aggregate_impact')}")

        if args.scenario in ["all", "hostel"]:
            print("\n" + "=" * 75)
            print("ANN-DAAN AI: Executing Section 20 Jaipur College Hostel Demo Scenario")
            print("=" * 75)
            res_h = run_demonstration_scenario(db)
            print("\n[SUCCESS] Section 20 Scenario Completed:")
            for k, v in res_h.items():
                print(f"  * {k}: {v}")

    finally:
        db.close()
    print("\n" + "=" * 75)
