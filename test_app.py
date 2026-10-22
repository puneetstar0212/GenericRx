import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import app
from app.database import Base, get_db
from app.seed_database import seed_db

# Create a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_genericrx.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    # Setup
    Base.metadata.create_all(bind=engine)
    # Use the existing seed function but redirect it to use the test engine/session if needed
    # Actually, seed_db in seed_database.py uses the default SessionLocal. 
    # Let's just create a local session and insert dummy data, or patch seed_db.
    # A quick way is to just let the main app use the test DB.
    
    # We will manually seed the test db with some data for testing
    from app.models import Medicine, Pharmacy
    db = TestingSessionLocal()
    if db.query(Medicine).count() == 0:
        db.add(Medicine(
            name="Crocin",
            salt_name="Paracetamol",
            dosage_form="Tablet",
            strength="500mg",
            manufacturer="GSK",
            unit_count=10,
            price_per_unit=1.50,
            is_generic=False,
            therapeutic_category="Analgesic"
        ))
        db.add(Medicine(
            name="Paracetamol (Jan Aushadhi)",
            salt_name="Paracetamol",
            dosage_form="Tablet",
            strength="500mg",
            manufacturer="BPPI",
            unit_count=10,
            price_per_unit=0.35,
            is_generic=True,
            therapeutic_category="Analgesic"
        ))
        db.add(Pharmacy(
            name="Jan Aushadhi Kendra - Downtown",
            address="123 Main St",
            city="Metropolis",
            lat=28.7041,
            lng=77.1025,
            pharmacy_type="Jan Aushadhi",
            phone="9876543210"
        ))
        db.commit()
    db.close()
    
    yield
    
    # Teardown
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_genericrx.db"):
        try:
            os.remove("./test_genericrx.db")
        except PermissionError:
            pass


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_get_all_medicines():
    response = client.get("/api/medicines")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    
def test_search_medicine():
    response = client.get("/api/search?q=Paracetamol")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "Paracetamol"
    assert data["count"] >= 2
    assert len(data["results"]) >= 2

def test_get_alternatives():
    # First find the ID of Crocin
    search_res = client.get("/api/search?q=Crocin").json()
    crocin_id = search_res["results"][0]["id"]
    
    # Now get alternatives
    response = client.get(f"/api/medicine/{crocin_id}/alternatives")
    assert response.status_code == 200
    data = response.json()
    assert data["targetMedicine"]["name"] == "Crocin"
    assert len(data["alternatives"]) >= 1
    assert data["alternatives"][0]["name"] == "Paracetamol (Jan Aushadhi)"
    assert data["alternatives"][0]["savingsPercentage"] > 0

def test_audit_prescription():
    # Find IDs
    search_res = client.get("/api/search?q=Crocin").json()
    crocin_id = search_res["results"][0]["id"]
    
    alt_res = client.get(f"/api/medicine/{crocin_id}/alternatives").json()
    generic_id = alt_res["alternatives"][0]["id"]
    
    payload = {
        "items": [
            {
                "medicine_id": crocin_id,
                "alternative_id": generic_id,
                "monthly_units": 30
            }
        ]
    }
    response = client.post("/api/audit-prescription", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "totalOriginalMonthly" in data
    assert "totalGenericMonthly" in data
    assert "totalMonthlySavings" in data
    assert "totalYearlySavings" in data
    assert data["totalMonthlySavings"] > 0

def test_get_nearby_pharmacies():
    response = client.get("/api/pharmacies/nearby?city=Metropolis")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["city"] == "Metropolis"

def test_get_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["totalMedicines"] >= 2
    assert data["genericCount"] >= 1
    assert data["totalPharmacies"] >= 1
