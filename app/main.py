import os
import sys
from fastapi import FastAPI, Depends, Query, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import get_db, engine, Base
from app.models import Medicine, Pharmacy
from app.search_engine import search_medicines, get_alternatives
from app.savings_engine import calculate_prescription_audit
from app.seed_database import seed_db

# Create DB tables if not existing and seed dataset
Base.metadata.create_all(bind=engine)
seed_db()

app = FastAPI(
    title="GenericRx API",
    description="Offline-First Medicine Alternative & Cost Audit System API",
    version="1.1.0"
)

# Enable CORS for PWA and client apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# Pydantic Schemas
class AuditItemSchema(BaseModel):
    medicine_id: int
    alternative_id: Optional[int] = None
    monthly_units: int = 30


class PrescriptionAuditRequest(BaseModel):
    items: List[AuditItemSchema]


# API Routes

@app.get("/")
async def serve_pwa_homepage(request: Request):
    """
    Renders main PWA Single-Page Application homepage.
    """
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/health")
def health_check():
    return {"status": "online", "system": "GenericRx Python API", "version": "1.1.0"}


@app.get("/api/medicines")
def get_all_medicines(db: Session = Depends(get_db)):
    """
    Returns full medicine dataset for initial PWA IndexedDB offline caching.
    """
    meds = db.query(Medicine).all()
    return [m.to_dict() for m in meds]


@app.get("/api/search")
def search_medicine_api(q: str = Query("", description="Brand name, Salt composition, or Category"), db: Session = Depends(get_db)):
    """
    Fuzzy search endpoint resolving Brand to Salt, Composition matching, and Typo Tolerance.
    """
    results = search_medicines(q, db, limit=50)
    return {
        "query": q,
        "count": len(results),
        "results": results
    }


@app.get("/api/medicine/{medicine_id}/alternatives")
def get_generic_alternatives_api(medicine_id: int, db: Session = Depends(get_db)):
    """
    Returns generic & brand alternatives sharing exact chemical salt composition,
    calculates savings % and flags dosage/strength mismatch warnings.
    """
    res = get_alternatives(medicine_id, db)
    if not res:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return res


@app.post("/api/audit-prescription")
def audit_prescription_api(payload: PrescriptionAuditRequest, db: Session = Depends(get_db)):
    """
    Computes monthly and annual cost savings for a list of prescribed medications.
    """
    items = [item.dict() for item in payload.items]
    audit_res = calculate_prescription_audit(items, db)
    return audit_res


@app.get("/api/pharmacies/nearby")
def get_nearby_pharmacies_api(
    city: Optional[str] = Query(None, description="Filter by city"),
    type: Optional[str] = Query(None, description="Filter by pharmacy type"),
    db: Session = Depends(get_db)
):
    """
    Returns nearby Jan Aushadhi Kendras and retail pharmacies with stock status and GPS coordinates.
    """
    query = db.query(Pharmacy)
    if city and city.strip():
        query = query.filter(Pharmacy.city.ilike(f"%{city.strip()}%"))
    if type and type.strip():
        query = query.filter(Pharmacy.pharmacy_type.ilike(f"%{type.strip()}%"))
    
    pharmacies = query.all()
    return [p.to_dict() for p in pharmacies]


@app.get("/api/stats")
def get_system_stats(db: Session = Depends(get_db)):
    """
    Returns dataset metadata statistics.
    """
    total = db.query(Medicine).count()
    generics = db.query(Medicine).filter(Medicine.is_generic == True).count()
    brands = total - generics
    salts_count = db.query(Medicine.salt_name).distinct().count()
    categories_count = db.query(Medicine.therapeutic_category).distinct().count()
    pharmacies_count = db.query(Pharmacy).count()

    return {
        "totalMedicines": total,
        "genericCount": generics,
        "brandCount": brands,
        "distinctSalts": salts_count,
        "distinctCategories": categories_count,
        "totalPharmacies": pharmacies_count
    }
