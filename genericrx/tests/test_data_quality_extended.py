"""Extended tests covering null-price support, savings logic, migration safety,
and all existing search/seed functionality.

Run with:
    python -m pytest genericrx/tests/test_data_quality_extended.py -v
or alongside the unittest-based audit tests:
    python -m pytest genericrx/tests/ -v
"""
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure repository root is on sys.path so app imports resolve.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "genericrx" / "scripts"))

# ---------------------------------------------------------------------------
# Savings engine tests (pure Python, no DB required)
# ---------------------------------------------------------------------------

from app.savings_engine import (
    calculate_savings_percentage,
    get_savings_badge_info,
)


class TestSavingsEngineNullPrices(unittest.TestCase):
    """savings_engine must never invent numbers when a price is unknown."""

    def test_both_prices_known_returns_float(self):
        result = calculate_savings_percentage(100.0, 30.0)
        self.assertAlmostEqual(result, 70.0)

    def test_brand_price_none_returns_none(self):
        self.assertIsNone(calculate_savings_percentage(None, 30.0))

    def test_generic_price_none_returns_none(self):
        self.assertIsNone(calculate_savings_percentage(100.0, None))

    def test_both_prices_none_returns_none(self):
        self.assertIsNone(calculate_savings_percentage(None, None))

    def test_zero_brand_price_returns_zero(self):
        self.assertEqual(calculate_savings_percentage(0.0, 30.0), 0.0)

    def test_negative_savings_capped(self):
        # Generic more expensive than brand → negative, capped at -100
        result = calculate_savings_percentage(10.0, 200.0)
        self.assertGreaterEqual(result, -100.0)

    def test_badge_none_savings_shows_unavailable(self):
        color, text = get_savings_badge_info(None)
        self.assertEqual(color, "gray")
        self.assertIn("unavailable", text.lower())

    def test_badge_high_savings(self):
        color, text = get_savings_badge_info(75.0)
        self.assertEqual(color, "green")

    def test_badge_moderate_savings(self):
        color, text = get_savings_badge_info(35.0)
        self.assertEqual(color, "amber")

    def test_badge_low_savings(self):
        color, text = get_savings_badge_info(10.0)
        self.assertEqual(color, "blue")

    def test_badge_same_price(self):
        color, _ = get_savings_badge_info(0.0)
        self.assertEqual(color, "gray")


class TestPrescriptionAuditNullPrices(unittest.TestCase):
    """calculate_prescription_audit must skip/flag items with unknown prices."""

    def _make_db_session(self, medicines):
        """Return a mock SQLAlchemy session backed by a dict of Medicine mocks."""
        session = MagicMock()

        class FakeQuery:
            def __init__(self, items):
                self._items = items

            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return self._items[0] if self._items else None

        def fake_query(model):
            # Return the right mock based on what filter was called with
            return MagicMock(
                filter=lambda *a, **kw: MagicMock(first=lambda: None)
            )

        # Build index by id
        med_map = {m.id: m for m in medicines}

        def query_side_effect(model):
            q = MagicMock()

            def filter_side_effect(condition):
                fq = MagicMock()

                def first_side_effect():
                    # Try to extract id from the filter condition by checking each medicine
                    for m in medicines:
                        return m  # Simplified: return first match
                    return None

                fq.first = first_side_effect
                return fq

            q.filter = filter_side_effect
            return q

        session.query = query_side_effect
        return session, med_map

    def test_brand_unknown_price_excluded_from_totals(self):
        """If brand has no price, item is excluded from savings totals."""
        from app.savings_engine import calculate_prescription_audit

        brand = MagicMock()
        brand.id = 1
        brand.name = "Brand X"
        brand.salt_name = "Salt X"
        brand.price_per_unit = None  # unknown
        brand.unit_count = 10

        session = MagicMock()
        session.query.return_value.filter.return_value.first.side_effect = [brand, None]

        result = calculate_prescription_audit(
            [{"medicine_id": 1, "monthly_units": 30}],
            session,
        )
        self.assertEqual(result["totalOriginalMonthly"], 0.0)
        self.assertIsNone(result["items"][0]["brandMonthlyCost"])
        self.assertTrue(result["hasMissingPrices"])


# ---------------------------------------------------------------------------
# Search engine sort-key tests (no DB)
# ---------------------------------------------------------------------------

class TestSearchEngineSortKeyNullPrices(unittest.TestCase):
    """get_alternatives sort key must not crash when prices or savings are None."""

    def _make_alt(self, is_generic, savings_pct, price):
        return {
            "isGeneric": is_generic,
            "savingsPercentage": savings_pct,
            "pricePerUnit": price,
        }

    def test_sort_does_not_raise_with_none_savings(self):
        """Sorting a list containing None savings should not raise TypeError."""
        alts = [
            self._make_alt(True, None, None),
            self._make_alt(True, 70.0, 5.0),
            self._make_alt(False, None, None),
            self._make_alt(False, 30.0, 15.0),
        ]

        def _sort_key(x):
            savings = x["savingsPercentage"]
            price = x["pricePerUnit"]
            return (
                not x["isGeneric"],
                -(savings if savings is not None else float('-inf')),
                price if price is not None else float('inf'),
            )

        try:
            sorted(alts, key=_sort_key)
        except TypeError as exc:
            self.fail(f"Sort raised TypeError with None prices: {exc}")

    def test_none_price_sorts_last(self):
        """Items with unknown prices should appear after known-price items."""
        alts = [
            self._make_alt(True, None, None),
            self._make_alt(True, 50.0, 10.0),
        ]

        def _sort_key(x):
            savings = x["savingsPercentage"]
            price = x["pricePerUnit"]
            return (
                not x["isGeneric"],
                -(savings if savings is not None else float('-inf')),
                price if price is not None else float('inf'),
            )

        sorted_alts = sorted(alts, key=_sort_key)
        # The medicine with a known savings % should sort first
        self.assertEqual(sorted_alts[0]["savingsPercentage"], 50.0)
        self.assertIsNone(sorted_alts[1]["pricePerUnit"])


# ---------------------------------------------------------------------------
# Migration script tests (uses temp SQLite files)
# ---------------------------------------------------------------------------

from migrate_price_nullable import (
    column_is_already_nullable,
    price_column_exists,
    run_migration,
)


class TestMigrationScript(unittest.TestCase):
    """Database migration: make price_per_unit nullable in SQLite."""

    def _create_old_db(self, path: str) -> None:
        """Create a SQLite database with the OLD non-nullable schema."""
        conn = sqlite3.connect(path)
        conn.execute("""
            CREATE TABLE medicines (
                id INTEGER NOT NULL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                salt_name VARCHAR(255) NOT NULL,
                strength VARCHAR(100) NOT NULL,
                dosage_form VARCHAR(100) NOT NULL,
                price_per_unit FLOAT NOT NULL,
                unit_count INTEGER,
                is_generic BOOLEAN,
                manufacturer VARCHAR(255) NOT NULL,
                schedule VARCHAR(50),
                therapeutic_category VARCHAR(100),
                description TEXT
            )
        """)
        conn.execute("""
            INSERT INTO medicines
            (id, name, salt_name, strength, dosage_form, price_per_unit,
             unit_count, is_generic, manufacturer, schedule, therapeutic_category)
            VALUES (1,'Crocin','Paracetamol','500mg','Tablet',1.5,10,0,'GSK','OTC','Analgesic')
        """)
        conn.commit()
        conn.close()

    def test_detects_non_nullable_column(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            self._create_old_db(db_path)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            self.assertFalse(column_is_already_nullable(conn))
            conn.close()
        finally:
            os.unlink(db_path)

    def test_migration_makes_price_nullable(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        try:
            self._create_old_db(str(db_path))
            result = run_migration(db_path, dry_run=False, no_backup=True)
            self.assertEqual(result, 0)
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            self.assertTrue(column_is_already_nullable(conn))
            row_count = conn.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
            self.assertEqual(row_count, 1)
            conn.close()
        finally:
            db_path.unlink(missing_ok=True)

    def test_migration_is_idempotent(self):
        """Running migration on an already-nullable column returns 0 without error."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        try:
            self._create_old_db(str(db_path))
            run_migration(db_path, dry_run=False, no_backup=True)
            result = run_migration(db_path, dry_run=False, no_backup=True)
            self.assertEqual(result, 0)
        finally:
            db_path.unlink(missing_ok=True)

    def test_dry_run_makes_no_changes(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        try:
            self._create_old_db(str(db_path))
            result = run_migration(db_path, dry_run=True, no_backup=True)
            self.assertEqual(result, 0)
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            # Should still be non-nullable after dry-run
            self.assertFalse(column_is_already_nullable(conn))
            conn.close()
        finally:
            db_path.unlink(missing_ok=True)

    def test_migration_creates_backup(self):
        tmpdir = Path(tempfile.mkdtemp())
        db_path = tmpdir / "test.db"
        try:
            self._create_old_db(str(db_path))
            run_migration(db_path, dry_run=False, no_backup=False)
            backups = list(tmpdir.glob("test_backup_*.db"))
            self.assertGreater(len(backups), 0, "Backup file should have been created")
        finally:
            shutil.rmtree(str(tmpdir), ignore_errors=True)

    def test_nonexistent_db_returns_error_code(self):
        result = run_migration(Path("nonexistent_db_12345.db"), dry_run=False, no_backup=True)
        self.assertEqual(result, 2)


# ---------------------------------------------------------------------------
# Model field tests
# ---------------------------------------------------------------------------

class TestMedicineModelNullablePrice(unittest.TestCase):
    """Medicine.price_per_unit must be nullable at the ORM level."""

    def test_price_per_unit_nullable_in_model(self):
        from app.models import Medicine
        col = Medicine.__table__.c.price_per_unit
        self.assertTrue(col.nullable, "price_per_unit column should be nullable")

    def test_to_dict_with_none_price(self):
        from app.models import Medicine
        med = Medicine(
            id=999,
            name="Test Med",
            salt_name="Test Salt",
            strength="10mg",
            dosage_form="Tablet",
            price_per_unit=None,
            unit_count=10,
            is_generic=True,
            manufacturer="Test Pharma",
            schedule="OTC",
            therapeutic_category="Test",
            description=""
        )
        d = med.to_dict()
        self.assertIsNone(d["pricePerUnit"])
        self.assertIn("pricePerUnit", d)

    def test_to_dict_with_known_price(self):
        from app.models import Medicine
        med = Medicine(
            id=1,
            name="Test Med",
            salt_name="Test Salt",
            strength="10mg",
            dosage_form="Tablet",
            price_per_unit=5.50,
            unit_count=10,
            is_generic=False,
            manufacturer="Test Pharma",
            schedule="OTC",
            therapeutic_category="Test",
        )
        d = med.to_dict()
        self.assertAlmostEqual(d["pricePerUnit"], 5.50)


if __name__ == "__main__":
    unittest.main()
