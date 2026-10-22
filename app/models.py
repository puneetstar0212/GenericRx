from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from app.database import Base


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    salt_name = Column(String(255), nullable=False, index=True)
    strength = Column(String(100), nullable=False)
    dosage_form = Column(String(100), nullable=False)  # Tablet, Syrup, Injection, Capsule, Ointment
    # price_per_unit is nullable: unknown/unverified prices must be stored as NULL,
    # never as zero or an estimated value.
    price_per_unit = Column(Float, nullable=True)  # Price in INR; None means unknown/unverified
    unit_count = Column(Integer, default=10)        # Number of units per strip/bottle
    is_generic = Column(Boolean, default=False, index=True)
    manufacturer = Column(String(255), nullable=False)
    schedule = Column(String(50), default="OTC")    # OTC, Schedule H, Schedule H1, Schedule X
    therapeutic_category = Column(String(100), index=True)
    description = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "saltName": self.salt_name,
            "strength": self.strength,
            "dosageForm": self.dosage_form,
            # None is returned as-is; API consumers must treat null as "price unavailable".
            "pricePerUnit": self.price_per_unit,
            "unitCount": self.unit_count,
            "isGeneric": self.is_generic,
            "manufacturer": self.manufacturer,
            "schedule": self.schedule,
            "therapeuticCategory": self.therapeutic_category,
            "description": self.description or ""
        }


class Pharmacy(Base):
    __tablename__ = "pharmacies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    pharmacy_type = Column(String(100), nullable=False, index=True)  # Jan Aushadhi Kendra, Retail Pharmacy
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    is_open_24h = Column(Boolean, default=False)
    stock_status = Column(String(255), default="Full Stock (Generics & Brands)")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.pharmacy_type,
            "address": self.address,
            "city": self.city,
            "phone": self.phone,
            "lat": self.lat,
            "lng": self.lng,
            "isOpen24h": self.is_open_24h,
            "stockStatus": self.stock_status
        }
