import urllib.request
import json
import os
import sys
from random import uniform

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models import Medicine

FDA_API_URL = "https://api.fda.gov/drug/ndc.json?limit=500"

def fetch_and_import_fda_data():
    print(f"Fetching official medicine data from OpenFDA: {FDA_API_URL}")
    req = urllib.request.Request(FDA_API_URL, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        results = data.get("results", [])
    except Exception as e:
        print(f"Failed to fetch data from OpenFDA: {e}")
        return

    print(f"Successfully fetched {len(results)} records. Processing and importing to database...")
    
    db = SessionLocal()
    
    added_count = 0
    skipped_count = 0

    for item in results:
        brand_name = item.get("brand_name", "")
        generic_name = item.get("generic_name", "")
        
        # Skip if missing essential names
        if not brand_name or not generic_name:
            skipped_count += 1
            continue
            
        dosage_form = item.get("dosage_form", "Tablet").title()
        
        # Extract active ingredients and strengths
        active_ingredients = item.get("active_ingredients", [])
        if active_ingredients:
            strength = " + ".join([ing.get("strength", "") for ing in active_ingredients])
        else:
            strength = "Standard"
            
        manufacturer = item.get("labeler_name", "Unknown Official Source")
        product_type = item.get("product_type", "HUMAN PRESCRIPTION DRUG")
        
        schedule = "Schedule H" if "PRESCRIPTION" in product_type.upper() else "OTC"
        
        category = item.get("pharm_class", ["General Therapeutic"])[0] if item.get("pharm_class") else "General Therapeutic"
        
        # OpenFDA doesn't have prices, so we simulate realistic INR pricing based on product type
        base_price = round(uniform(20.0, 300.0), 2)
        
        # Check if it already exists to avoid duplicates
        existing = db.query(Medicine).filter(Medicine.name == brand_name).first()
        if existing:
            skipped_count += 1
            continue

        # Branded Version
        med = Medicine(
            name=brand_name.title(),
            salt_name=generic_name.title(),
            strength=strength,
            dosage_form=dosage_form,
            price_per_unit=base_price,
            unit_count=10,
            is_generic=False,
            manufacturer=manufacturer.title(),
            schedule=schedule,
            therapeutic_category=category.title(),
            description="Imported from Official US FDA Database"
        )
        db.add(med)
        
        # Create a generic alternative version as well for the savings engine
        generic_med = Medicine(
            name=f"Generic {generic_name.split(' ')[0].title()} (Jan Aushadhi Equivalent)",
            salt_name=generic_name.title(),
            strength=strength,
            dosage_form=dosage_form,
            price_per_unit=round(base_price * 0.15, 2), # 85% cheaper generic
            unit_count=10,
            is_generic=True,
            manufacturer="BPPI / Generic Source",
            schedule=schedule,
            therapeutic_category=category.title(),
            description="Simulated official generic alternative"
        )
        # Avoid duplicate generic entries for same salt
        existing_generic = db.query(Medicine).filter(Medicine.name == generic_med.name).first()
        if not existing_generic:
            db.add(generic_med)
            
        added_count += 1
        
        # Commit in batches of 50
        if added_count % 50 == 0:
            db.commit()

    db.commit()
    db.close()
    
    print(f"Import complete. Added {added_count} brand and generic official medicines. Skipped {skipped_count}.")

if __name__ == "__main__":
    fetch_and_import_fda_data()
