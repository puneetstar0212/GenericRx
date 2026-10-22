#!/usr/bin/env python3
"""Read-only quality audit for GenericRx medicine seed data.

Run from the repository root:
    python genericrx/scripts/audit_medicine_seed.py

Optional custom input/output:
    python genericrx/scripts/audit_medicine_seed.py --input path/to/medicines_seed.json --output-dir audit-output

This tool never edits the seed file or database. Flags are review prompts, not automatic corrections.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REQUIRED_TEXT_FIELDS = (
    "name",
    "salt_name",
    "strength",
    "dosage_form",
    "manufacturer",
    "therapeutic_category",
)
PLACEHOLDER_MANUFACTURER_PATTERNS = (
    re.compile(r"^\s*pharma brand\s*\d*\s*$", re.I),
    re.compile(r"^\s*pmbjp generic pharma\s*$", re.I),
)
GENERIC_NAME_PATTERN = re.compile(r"\b(generic|jan\s*aushadhi|pmbjp)\b", re.I)


def normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def audit_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a reproducible audit summary and row-level review flags."""
    issue_counts: Counter[str] = Counter()
    findings: list[dict[str, Any]] = []
    seen_ids: set[Any] = set()
    normalized_names: dict[str, list[Any]] = defaultdict(list)

    for index, record in enumerate(records):
        issues: list[str] = []
        record_id = record.get("id")
        name = str(record.get("name") or "").strip()

        if record_id is None:
            issues.append("missing_id")
        elif record_id in seen_ids:
            issues.append("duplicate_id")
        else:
            seen_ids.add(record_id)

        for field in REQUIRED_TEXT_FIELDS:
            if not str(record.get(field) or "").strip():
                issues.append(f"missing_{field}")

        price = record.get("price_per_unit")
        if price is not None:
            if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
                issues.append("invalid_price")
        # A null price is allowed by the audit policy: unverified prices should be blank.
        # The current application schema may need a separate migration before it can store null.

        unit_count = record.get("unit_count")
        if unit_count is not None and (
            isinstance(unit_count, bool) or not isinstance(unit_count, int) or unit_count <= 0
        ):
            issues.append("invalid_unit_count")

        manufacturer = str(record.get("manufacturer") or "")
        if any(pattern.search(manufacturer) for pattern in PLACEHOLDER_MANUFACTURER_PATTERNS):
            issues.append("placeholder_or_unverified_manufacturer")

        form = normalize(record.get("dosage_form"))
        strength = normalize(record.get("strength"))
        salt_name = normalize(record.get("salt_name"))
        if "xl" in form.split() and re.search(r"\b1000\s*mg\b", strength):
            issues.append("strength_form_conflict_review")
        if "xl" in form.split() and not re.search(r"\b(xl|extended|prolonged|modified|release)\b", salt_name):
            issues.append("release_form_requires_review")

        if GENERIC_NAME_PATTERN.search(name) and record.get("is_generic") is False:
            issues.append("generic_label_flag_conflict")

        if name:
            normalized_names[normalize(name)].append(record_id if record_id is not None else index)

        if issues:
            for issue in issues:
                issue_counts[issue] += 1
            findings.append({
                "id": record_id,
                "name": name,
                "issues": issues,
                "source_index": index,
            })

    duplicate_name_groups = []
    for normalized_name, ids in sorted(normalized_names.items()):
        if len(ids) > 1:
            duplicate_name_groups.append({
                "normalized_name": normalized_name,
                "record_ids": ids,
                "count": len(ids),
            })

    for _group in duplicate_name_groups:
        issue_counts["duplicate_normalized_name_group"] += 1

    return {
        "record_count": len(records),
        "unique_id_count": len(seen_ids),
        "distinct_normalized_name_count": len(normalized_names),
        "duplicate_normalized_name_groups": duplicate_name_groups,
        "issue_counts": dict(sorted(issue_counts.items())),
        "flagged_record_count": len(findings),
        "findings": findings,
        "notes": [
            "This is a data-quality screening report, not clinical validation.",
            "A flagged field must be checked against a trustworthy source before correction.",
            "A null price means unknown/unverified; do not replace it with an estimated price.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("genericrx/data/medicines_seed.json"),
        help="Path to medicines_seed.json (default: genericrx/data/medicines_seed.json)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("genericrx/data_quality_report"),
        help="Directory for JSON and CSV reports (default: genericrx/data_quality_report)",
    )
    args = parser.parse_args()

    try:
        with args.input.open("r", encoding="utf-8") as handle:
            records = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not read valid JSON from {args.input}: {exc}", file=sys.stderr)
        return 2

    if not isinstance(records, list):
        print("Seed file must contain a JSON array of medicine objects.", file=sys.stderr)
        return 2
    if any(not isinstance(record, dict) for record in records):
        print("Every medicine record must be a JSON object.", file=sys.stderr)
        return 2

    report = audit_records(records)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "medicine_seed_audit.json"
    csv_path = args.output_dir / "medicine_seed_findings.csv"

    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "name", "issues", "source_index"])
        writer.writeheader()
        for finding in report["findings"]:
            writer.writerow({
                **finding,
                "issues": ";".join(finding["issues"]),
            })

    print(f"Records audited: {report['record_count']}")
    print(f"Unique IDs: {report['unique_id_count']}")
    print(f"Distinct normalized names: {report['distinct_normalized_name_count']}")
    print(f"Flagged records: {report['flagged_record_count']}")
    print("Issue counts:")
    for issue, count in report["issue_counts"].items():
        print(f"  {issue}: {count}")
    print(f"JSON report: {json_path}")
    print(f"CSV findings: {csv_path}")
    print("No medicine records or database rows were modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
