from sqlalchemy.orm import Session
from sqlalchemy import or_
from rapidfuzz import process, fuzz
from app.models import Medicine
from app.savings_engine import calculate_savings_percentage, get_savings_badge_info


def search_medicines(query: str, db: Session, limit: int = 50):
    """
    Intelligent fuzzy search across Brand Name, Salt Composition, and Category.
    """
    if not query or not query.strip():
        return [m.to_dict() for m in db.query(Medicine).limit(limit).all()]

    clean_query = query.strip().lower()

    # Exact or substring match in DB first
    exact_matches = db.query(Medicine).filter(
        or_(
            Medicine.name.ilike(f"%{clean_query}%"),
            Medicine.salt_name.ilike(f"%{clean_query}%"),
            Medicine.therapeutic_category.ilike(f"%{clean_query}%"),
            Medicine.manufacturer.ilike(f"%{clean_query}%")
        )
    ).all()

    if exact_matches and len(exact_matches) >= limit:
        return [m.to_dict() for m in exact_matches[:limit]]

    # If few substring matches, use rapidfuzz for spelling correction
    all_medicines = db.query(Medicine).all()
    all_names = [(m.id, f"{m.name} {m.salt_name} {m.therapeutic_category}") for m in all_medicines]

    # RapidFuzz match
    choices = [item[1] for item in all_names]
    fuzzy_results = process.extract(clean_query, choices, scorer=fuzz.WRatio, limit=limit)

    matched_ids = []
    # Add exact matches first
    for m in exact_matches:
        if m.id not in matched_ids:
            matched_ids.append(m.id)

    for match in fuzzy_results:
        # match structure: (choice_text, score, index)
        if match[1] > 45:  # threshold score
            med_id = all_names[match[2]][0]
            if med_id not in matched_ids:
                matched_ids.append(med_id)

    matched_meds = {m.id: m for m in all_medicines if m.id in matched_ids}
    ordered = [matched_meds[mid].to_dict() for mid in matched_ids if mid in matched_meds]
    return ordered[:limit]


def get_alternatives(medicine_id: int, db: Session):
    """
    Find alternatives for a given medicine matching exact active salt composition.
    Calculates cost savings %, visual audit badge, and dosage mismatch flags.
    """
    target = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not target:
        return None

    ref_price = target.price_per_unit

    # Query all medicines with similar salt name
    alternatives = db.query(Medicine).filter(
        Medicine.salt_name.ilike(f"%{target.salt_name.split('+')[0].strip()}%")
    ).all()

    processed_alternatives = []
    for alt in alternatives:
        if alt.id == target.id:
            continue

        savings_pct = calculate_savings_percentage(ref_price, alt.price_per_unit)
        badge_color, badge_text = get_savings_badge_info(savings_pct)

        # Dosage Mismatch Flag
        strength_mismatch = alt.strength.strip().lower() != target.strength.strip().lower()
        form_mismatch = alt.dosage_form.strip().lower() != target.dosage_form.strip().lower()
        has_mismatch = strength_mismatch or form_mismatch

        mismatch_reasons = []
        if strength_mismatch:
            mismatch_reasons.append(f"Strength difference ({alt.strength} vs {target.strength})")
        if form_mismatch:
            mismatch_reasons.append(f"Form difference ({alt.dosage_form} vs {target.dosage_form})")

        alt_dict = alt.to_dict()
        alt_dict["savingsPercentage"] = round(savings_pct, 1)
        alt_dict["savingsBadgeColor"] = badge_color
        alt_dict["savingsBadgeText"] = badge_text
        alt_dict["hasMismatch"] = has_mismatch
        alt_dict["mismatchWarning"] = "; ".join(mismatch_reasons) if has_mismatch else None

        processed_alternatives.append(alt_dict)

    # Sort: Generics first, then highest savings %
    processed_alternatives.sort(key=lambda x: (not x["isGeneric"], -x["savingsPercentage"], x["pricePerUnit"]))

    return {
        "targetMedicine": target.to_dict(),
        "saltName": target.salt_name,
        "alternatives": processed_alternatives,
        "count": len(processed_alternatives)
    }
