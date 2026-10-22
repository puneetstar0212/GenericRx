"""Structural and safety-policy tests for GenericRx seed data audit."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "genericrx" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from audit_medicine_seed import audit_records  # noqa: E402


class MedicineSeedAuditTests(unittest.TestCase):
    def test_flags_duplicate_ids_and_normalized_names(self):
        records = [
            {"id": 1, "name": "Test Med", "salt_name": "Example 5mg", "strength": "5mg",
             "dosage_form": "Tablet", "price_per_unit": 10, "unit_count": 10,
             "is_generic": False, "manufacturer": "Example Ltd", "schedule": "Schedule H",
             "therapeutic_category": "Example"},
            {"id": 1, "name": " test   med ", "salt_name": "Example 5mg", "strength": "5mg",
             "dosage_form": "Tablet", "price_per_unit": None, "unit_count": 10,
             "is_generic": False, "manufacturer": "Example Ltd", "schedule": "Schedule H",
             "therapeutic_category": "Example"},
        ]
        report = audit_records(records)
        self.assertEqual(report["record_count"], 2)
        self.assertEqual(report["unique_id_count"], 1)
        self.assertEqual(len(report["duplicate_normalized_name_groups"]), 1)
        self.assertEqual(report["issue_counts"]["duplicate_id"], 1)

    def test_null_price_is_not_flagged_as_invalid(self):
        record = {
            "id": 1, "name": "Example", "salt_name": "Example 5mg", "strength": "5mg",
            "dosage_form": "Tablet", "price_per_unit": None, "unit_count": 10,
            "is_generic": False, "manufacturer": "Example Ltd", "schedule": "Schedule H",
            "therapeutic_category": "Example",
        }
        report = audit_records([record])
        self.assertNotIn("invalid_price", report["issue_counts"])

    def test_flags_placeholder_manufacturer_and_suspicious_xl_strength(self):
        record = {
            "id": 1, "name": "Example 5", "salt_name": "Example 5mg", "strength": "1000mg",
            "dosage_form": "Tablet XL", "price_per_unit": 10, "unit_count": 10,
            "is_generic": False, "manufacturer": "Pharma Brand 1", "schedule": "Schedule H",
            "therapeutic_category": "Example",
        }
        report = audit_records([record])
        issues = report["findings"][0]["issues"]
        self.assertIn("placeholder_or_unverified_manufacturer", issues)
        self.assertIn("strength_form_conflict_review", issues)
        self.assertIn("release_form_requires_review", issues)

    def test_existing_seed_file_is_valid_json_array_with_unique_ids(self):
        seed_file = ROOT / "genericrx" / "data" / "medicines_seed.json"
        if not seed_file.exists():
            self.skipTest("Run from a complete GenericRx repository checkout.")
        records = json.loads(seed_file.read_text(encoding="utf-8"))
        self.assertIsInstance(records, list)
        self.assertTrue(all(isinstance(record, dict) for record in records))
        ids = [record.get("id") for record in records]
        self.assertEqual(len(ids), len(set(ids)), "Medicine IDs must be unique")


if __name__ == "__main__":
    unittest.main()
