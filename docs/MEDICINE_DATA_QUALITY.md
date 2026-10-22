# GenericRx medicine data quality and expansion plan

## Current baseline

The seed dataset is `genericrx/data/medicines_seed.json`. Run the audit tool from the repository root:

```bash
python genericrx/scripts/audit_medicine_seed.py
python -m unittest discover -s genericrx/tests -v
```

The audit creates:
- `genericrx/data_quality_report/medicine_seed_audit.json`
- `genericrx/data_quality_report/medicine_seed_findings.csv`

These reports are generated artifacts; review them before committing. The audit tool is read-only with respect to the source seed JSON and database.

## Policy for the India-focused catalogue

1. Do not invent brands, manufacturers, prices, pack sizes, regulatory schedules, or equivalence claims.
2. A price that has not been verified from a reliable source must be stored as unknown (`null`), not as zero or an estimate.
3. Record source name/URL and verification date for each sourced claim. Price evidence should have its own source and checked date.
4. Separate the active ingredient composition from the display name. For combination products, retain every active ingredient and its strength.
5. Do not call a product a Jan Aushadhi product or government-approved alternative without a source supporting that exact claim.
6. Do not recommend an alternative solely because one ingredient substring matches. Candidate alternatives must be reviewed for all ingredients, strength, dosage form, and release characteristics. A pharmacist/clinician should confirm clinical suitability.
7. Preserve the original data and maintain an audit trail when correcting records.

## Initial audit findings

The baseline audit of the current main-branch seed file found:
- 651 records and 651 unique IDs.
- 647 distinct normalized medicine names, with 4 duplicate-name groups.
- 288 manufacturer values matched placeholder/unverified labels used by the current data.
- 100 records matched the screening rule for a `Tablet XL` form with `1000mg` strength.
- 100 `Tablet XL` records were flagged for release-form review.

These are screening results, not proof that all flagged records are incorrect. Check the generated CSV for individual IDs and names. In particular, the placeholder string `PMBJP Generic Pharma` must not be treated as a verified manufacturer. Do not bulk-replace it with a guessed company.

## 300-formulation expansion workflow

Build the expansion in reviewable batches rather than inserting 300 unverified records at once.

For every proposed formulation, require:
- normalized product/brand name (where applicable);
- all active ingredients and individual ingredient strengths;
- total strength and dosage form;
- immediate/modified/extended-release characteristics, where applicable;
- manufacturer/marketer only when verified;
- pack size and price only when verified;
- prescription schedule/status only when verified;
- source URL/name and date checked;
- review status (`draft`, `needs_review`, `verified`, or `rejected`).

Do not count brand variants as distinct formulations unless the formulation or relevant product identity is genuinely distinct. Track the target as 300 distinct formulations, not merely 300 rows.

## Application changes needed before nullable prices are imported

The current SQLAlchemy `Medicine.price_per_unit` column is non-nullable and the UI/savings logic may assume every price is numeric. Before storing unknown prices as `null`:
1. make the model field nullable;
2. apply a real database migration for existing SQLite/PostgreSQL databases (SQLAlchemy `create_all` does not alter existing columns);
3. update API serialization and UI rendering to show “Price not verified” instead of `₹0` or `NaN`;
4. update savings calculation and sorting so comparisons are omitted when either price is unknown;
5. add tests for missing prices, zero prices, and price comparisons.

Do not deploy a seed file containing `null` prices until the model, migration, API, and UI support them.

## Safety and trust

GenericRx is an information/comparison tool, not a diagnosis or prescribing service. Prescription medicines, antibiotics, and controlled medicines must be clearly labelled according to verified Indian requirements. Do not instruct users to start, stop, or substitute a prescribed medicine without a qualified professional.
