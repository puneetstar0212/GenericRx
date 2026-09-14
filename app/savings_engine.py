def calculate_savings_percentage(brand_price: float, generic_price: float) -> float:
    """
    Computes direct savings percentage using formula:
    Savings % = ((Brand Price - Generic Price) / Brand Price) * 100
    """
    if brand_price <= 0:
        return 0.0
    savings = ((brand_price - generic_price) / brand_price) * 100.0
    return max(-100.0, savings)  # Cap at -100 if generic is more expensive


def get_savings_badge_info(savings_percentage: float):
    """
    Determines visual audit indicator badge color and label.
    Green badge (> 50% savings)
    Amber badge (20-50% savings)
    Blue/Neutral badge (< 20% savings)
    """
    if savings_percentage >= 50.0:
        return "green", f"High Savings ({savings_percentage:.1f}%)"
    elif savings_percentage >= 20.0:
        return "amber", f"Moderate Savings ({savings_percentage:.1f}%)"
    elif savings_percentage > 0.0:
        return "blue", f"Low Savings ({savings_percentage:.1f}%)"
    else:
        return "gray", "Same / Higher Price"


def calculate_prescription_audit(items: list, db_session):
    """
    Calculates monthly and yearly savings for a list of prescribed medicines.
    items format: [{"medicine_id": 1, "alternative_id": 5, "monthly_units": 30}]
    """
    from app.models import Medicine

    audit_summary = []
    total_original_monthly = 0.0
    total_generic_monthly = 0.0

    for item in items:
        brand = db_session.query(Medicine).filter(Medicine.id == item["medicine_id"]).first()
        generic = db_session.query(Medicine).filter(Medicine.id == item["alternative_id"]).first() if item.get("alternative_id") else None

        if not brand:
            continue

        units = item.get("monthly_units", 30)
        # Price calculation per unit / strip
        brand_unit_cost = brand.price_per_unit / max(1, brand.unit_count)
        orig_monthly = brand_unit_cost * units

        if generic:
            gen_unit_cost = generic.price_per_unit / max(1, generic.unit_count)
            gen_monthly = gen_unit_cost * units
        else:
            gen_unit_cost = brand_unit_cost
            gen_monthly = orig_monthly

        monthly_savings = orig_monthly - gen_monthly
        item_savings_pct = calculate_savings_percentage(orig_monthly, gen_monthly)
        badge_color, badge_text = get_savings_badge_info(item_savings_pct)

        total_original_monthly += orig_monthly
        total_generic_monthly += gen_monthly

        audit_summary.append({
            "brandName": brand.name,
            "saltName": brand.salt_name,
            "brandMonthlyCost": round(orig_monthly, 2),
            "genericName": generic.name if generic else "No alternative selected",
            "genericMonthlyCost": round(gen_monthly, 2),
            "monthlySavings": round(monthly_savings, 2),
            "savingsPct": round(item_savings_pct, 1),
            "badgeColor": badge_color,
            "badgeText": badge_text,
            "units": units
        })

    total_monthly_savings = total_original_monthly - total_generic_monthly
    overall_savings_pct = calculate_savings_percentage(total_original_monthly, total_generic_monthly)
    overall_badge_color, overall_badge_text = get_savings_badge_info(overall_savings_pct)

    return {
        "items": audit_summary,
        "totalOriginalMonthly": round(total_original_monthly, 2),
        "totalGenericMonthly": round(total_generic_monthly, 2),
        "totalMonthlySavings": round(total_monthly_savings, 2),
        "totalOriginalYearly": round(total_original_monthly * 12, 2),
        "totalGenericYearly": round(total_generic_monthly * 12, 2),
        "totalYearlySavings": round(total_monthly_savings * 12, 2),
        "overallSavingsPercentage": round(overall_savings_pct, 1),
        "overallBadgeColor": overall_badge_color,
        "overallBadgeText": overall_badge_text
    }
