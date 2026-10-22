#!/usr/bin/env python3
"""Safe SQLite migration: make price_per_unit nullable.

This script backs up the existing database, then uses ALTER TABLE to add a new
nullable price_per_unit column, copies existing data across, and swaps columns.
Because SQLite does not support ALTER COLUMN directly, we use the standard
workaround: create a new table, copy data, drop the old table, rename.

Run from the repository root:
    python genericrx/scripts/migrate_price_nullable.py

Options:
    --db-path      Path to the SQLite database file (default: genericrx.db)
    --dry-run      Print planned steps without modifying the database.
    --no-backup    Skip the automatic backup (not recommended for production).
"""
from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


# SQLite-compatible schema for the medicines table with nullable price_per_unit.
_CREATE_MEDICINES_TEMP = """
CREATE TABLE medicines_new (
    id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    salt_name VARCHAR(255) NOT NULL,
    strength VARCHAR(100) NOT NULL,
    dosage_form VARCHAR(100) NOT NULL,
    price_per_unit FLOAT,
    unit_count INTEGER,
    is_generic BOOLEAN,
    manufacturer VARCHAR(255) NOT NULL,
    schedule VARCHAR(50),
    therapeutic_category VARCHAR(100),
    description TEXT,
    PRIMARY KEY (id)
)
"""

_COPY_DATA = """
INSERT INTO medicines_new
    (id, name, salt_name, strength, dosage_form, price_per_unit,
     unit_count, is_generic, manufacturer, schedule, therapeutic_category, description)
SELECT id, name, salt_name, strength, dosage_form, price_per_unit,
       unit_count, is_generic, manufacturer, schedule, therapeutic_category, description
FROM medicines
"""


def get_column_info(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.execute("PRAGMA table_info(medicines)")
    return [dict(row) for row in cur.fetchall()]


def column_is_already_nullable(conn: sqlite3.Connection) -> bool:
    """Return True if price_per_unit is already nullable (notnull == 0)."""
    for col in get_column_info(conn):
        if col["name"] == "price_per_unit":
            return col["notnull"] == 0
    return False


def price_column_exists(conn: sqlite3.Connection) -> bool:
    return any(c["name"] == "price_per_unit" for c in get_column_info(conn))


def run_migration(db_path: Path, dry_run: bool, no_backup: bool) -> int:
    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}", file=sys.stderr)
        return 2

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        if not price_column_exists(conn):
            print("ERROR: medicines table does not have a price_per_unit column. Aborting.", file=sys.stderr)
            return 2

        if column_is_already_nullable(conn):
            print("price_per_unit is already nullable. No migration needed.")
            return 0

        print(f"Database: {db_path}")
        row_count = conn.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
        print(f"Existing medicine records: {row_count}")

        if not no_backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = db_path.with_name(f"{db_path.stem}_backup_{timestamp}{db_path.suffix}")
            if dry_run:
                print(f"[DRY RUN] Would back up database to: {backup_path}")
            else:
                conn.close()
                shutil.copy2(str(db_path), str(backup_path))
                print(f"Backed up database to: {backup_path}")
                conn = sqlite3.connect(str(db_path))
                conn.row_factory = sqlite3.Row

        steps = [
            ("Create replacement table with nullable price_per_unit", _CREATE_MEDICINES_TEMP),
            ("Copy all data from medicines to medicines_new", _COPY_DATA),
            ("Drop old medicines table", "DROP TABLE medicines"),
            ("Rename medicines_new to medicines", "ALTER TABLE medicines_new RENAME TO medicines"),
            ("Recreate index on name", "CREATE INDEX IF NOT EXISTS ix_medicines_name ON medicines (name)"),
            ("Recreate index on salt_name", "CREATE INDEX IF NOT EXISTS ix_medicines_salt_name ON medicines (salt_name)"),
            ("Recreate index on is_generic", "CREATE INDEX IF NOT EXISTS ix_medicines_is_generic ON medicines (is_generic)"),
            ("Recreate index on therapeutic_category", "CREATE INDEX IF NOT EXISTS ix_medicines_therapeutic_category ON medicines (therapeutic_category)"),
        ]

        if dry_run:
            print("\n[DRY RUN] Steps that WOULD be executed:")
            for i, (desc, sql) in enumerate(steps, 1):
                print(f"  {i}. {desc}")
                print(f"     {sql.strip()[:80]}{'...' if len(sql.strip()) > 80 else ''}")
            print("\n[DRY RUN] No changes made.")
            return 0

        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("BEGIN EXCLUSIVE")
        try:
            for desc, sql in steps:
                print(f"  -> {desc}")
                conn.execute(sql)
            conn.commit()
        except Exception as exc:
            conn.rollback()
            print(f"ERROR during migration, rolled back: {exc}", file=sys.stderr)
            return 1
        finally:
            conn.execute("PRAGMA foreign_keys = ON")

        # Verify
        after_count = conn.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
        is_now_nullable = column_is_already_nullable(conn)
        print(f"\nMigration complete.")
        print(f"  Records preserved: {after_count} (was {row_count})")
        print(f"  price_per_unit nullable: {is_now_nullable}")
        if after_count != row_count:
            print("WARNING: Row count changed during migration!", file=sys.stderr)
            return 1
        return 0

    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("genericrx.db"),
        help="Path to the SQLite database (default: genericrx.db in cwd)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show steps without modifying the database.")
    parser.add_argument("--no-backup", action="store_true", help="Skip automatic database backup.")
    args = parser.parse_args()

    return run_migration(args.db_path, args.dry_run, args.no_backup)


if __name__ == "__main__":
    raise SystemExit(main())
