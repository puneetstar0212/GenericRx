import os
import json
from app.database import engine, Base, SessionLocal
from app.models import Medicine, Pharmacy

SEED_PHARMACIES = [
    {
        "name": "Pradhan Mantri Jan Aushadhi Kendra - Central Hospital Gate",
        "pharmacy_type": "Jan Aushadhi Kendra",
        "address": "Gate No. 2, Near Civil Hospital, MG Road",
        "city": "Mumbai",
        "phone": "+91 98201 12345",
        "lat": 19.0760,
        "lng": 72.8777,
        "is_open_24h": True,
        "stock_status": "Jan Aushadhi Generics: Paracetamol, Amoxicillin, Metformin, Pantoprazole (In Stock)"
    },
    {
        "name": "PMBJP Jan Aushadhi Store - Railway Station Complex",
        "pharmacy_type": "Jan Aushadhi Kendra",
        "address": "Platform 1 Exit, Central Station",
        "city": "Mumbai",
        "phone": "+91 98202 54321",
        "lat": 19.0820,
        "lng": 72.8820,
        "is_open_24h": False,
        "stock_status": "Full Jan Aushadhi Generic Range & Antidiabetics Available"
    },
    {
        "name": "Apollo Pharmacy 24/7 Emergency",
        "pharmacy_type": "Retail Pharmacy",
        "address": "Shop 4, Sunshine Towers, Dadar West",
        "city": "Mumbai",
        "phone": "+91 22 2410 9999",
        "lat": 19.0178,
        "lng": 72.8478,
        "is_open_24h": True,
        "stock_status": "Full Brand & Generic Stock (Crocin, Augmentin, Dolo, Pan-40)"
    },
    {
        "name": "MedPlus Chemist & Druggist",
        "pharmacy_type": "Retail Pharmacy",
        "address": "12, Commercial Plaza, Bandra West",
        "city": "Mumbai",
        "phone": "+91 22 2640 8888",
        "lat": 19.0596,
        "lng": 72.8295,
        "is_open_24h": False,
        "stock_status": "Brand & Equivalent Generics Available (15% Discount on Generics)"
    },
    {
        "name": "Jan Aushadhi Kendra - Connaught Place",
        "pharmacy_type": "Jan Aushadhi Kendra",
        "address": "Block C, Inner Circle, Connaught Place",
        "city": "Delhi",
        "phone": "+91 98100 98765",
        "lat": 28.6304,
        "lng": 77.2177,
        "is_open_24h": True,
        "stock_status": "Government Subsidized Generics: Paracetamol, Azithromycin, Telmisartan"
    },
    {
        "name": "Wellness Forever 24x7 Pharmacy",
        "pharmacy_type": "Retail Pharmacy",
        "address": "Near AIIMS Main Gate, Ring Road",
        "city": "Delhi",
        "phone": "+91 11 2658 7777",
        "lat": 28.5672,
        "lng": 77.2100,
        "is_open_24h": True,
        "stock_status": "Full Range of Emergency Prescription & Critical Care Meds"
    },
    {
        "name": "Jan Aushadhi Kendra - MG Road Metro",
        "pharmacy_type": "Jan Aushadhi Kendra",
        "address": "Exit Gate 3, MG Road Station",
        "city": "Bangalore",
        "phone": "+91 98450 11223",
        "lat": 12.9716,
        "lng": 77.5946,
        "is_open_24h": False,
        "stock_status": "Jan Aushadhi Generics & Chronic Care Medication"
    },
    {
        "name": "MedPlus Pharmacy 24 Hours",
        "pharmacy_type": "Retail Pharmacy",
        "address": "Indiranagar 100ft Road",
        "city": "Bangalore",
        "phone": "+91 80 2520 3344",
        "lat": 12.9784,
        "lng": 77.6408,
        "is_open_24h": True,
        "stock_status": "Full Stock: Generics, Brands & OTC Health Supplements"
    }
]


def seed_db():
    print("Initializing SQLite Database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        med_count = db.query(Medicine).count()
        if med_count == 0:
            seed_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "medicines_seed.json")
            if os.path.exists(seed_file):
                with open(seed_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                print(f"Seeding {len(data)} medicines into SQLite...")
                for item in data:
                    med = Medicine(
                        id=item["id"],
                        name=item["name"],
                        salt_name=item["salt_name"],
                        strength=item["strength"],
                        dosage_form=item["dosage_form"],
                        # Preserve null prices — do not substitute zero for unknown prices.
                        price_per_unit=item.get("price_per_unit"),
                        unit_count=item.get("unit_count", 10),
                        is_generic=item["is_generic"],
                        manufacturer=item["manufacturer"],
                        schedule=item.get("schedule", "OTC"),
                        therapeutic_category=item.get("therapeutic_category", "General"),
                        description=item.get("description", "")
                    )
                    db.add(med)
                db.commit()

        pharm_count = db.query(Pharmacy).count()
        if pharm_count == 0:
            print(f"Seeding {len(SEED_PHARMACIES)} pharmacy store locations into SQLite...")
            for p in SEED_PHARMACIES:
                pharm = Pharmacy(
                    name=p["name"],
                    pharmacy_type=p["pharmacy_type"],
                    address=p["address"],
                    city=p["city"],
                    phone=p["phone"],
                    lat=p["lat"],
                    lng=p["lng"],
                    is_open_24h=p["is_open_24h"],
                    stock_status=p["stock_status"]
                )
                db.add(pharm)
            db.commit()
            print("Successfully seeded pharmacy store locations.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()
