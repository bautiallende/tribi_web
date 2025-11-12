import json
import os

from ..db.session import SessionLocal, engine
from ..models import Base, Country, Carrier, Plan


def load_seed_data() -> dict:
    """Load seed data from JSON file."""
    seed_file = os.path.join(os.path.dirname(__file__), "seed_data.json")
    with open(seed_file, "r") as f:
        return json.load(f)


def seed_database():
    """
    Populate database with seed data.
    Creates all tables and inserts countries, carriers, and plans.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Load seed data
        data = load_seed_data()

        # Check if countries already exist
        existing_countries = db.query(Country).count()
        if existing_countries > 0:
            print(f"✓ Database already seeded ({existing_countries} countries found). Skipping.")
            return

        print("🌱 Seeding database...")

        # Insert countries
        countries_map = {}
        for country_data in data["countries"]:
            country = Country(**country_data)
            db.add(country)
            db.flush()
            countries_map[country_data["iso2"]] = country
        print(f"✓ Inserted {len(countries_map)} countries")

        # Insert carriers
        carriers_map = {}
        for carrier_data in data["carriers"]:
            carrier = Carrier(**carrier_data)
            db.add(carrier)
            db.flush()
            carriers_map[carrier_data["name"]] = carrier
        print(f"✓ Inserted {len(carriers_map)} carriers")

        # Insert plans
        for plan_data in data["plans"]:
            country_iso2 = plan_data.pop("country_iso2")
            carrier_name = plan_data.pop("carrier_name")

            country = countries_map.get(country_iso2)
            carrier = carriers_map.get(carrier_name)

            if not country or not carrier:
                print(f"⚠ Skipping plan (missing country or carrier): {plan_data}")
                continue

            plan = Plan(
                country_id=country.id,
                carrier_id=carrier.id,
                **plan_data,
            )
            db.add(plan)

        db.commit()
        plan_count = db.query(Plan).count()
        print(f"✓ Inserted {plan_count} plans")
        print("✓ Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
