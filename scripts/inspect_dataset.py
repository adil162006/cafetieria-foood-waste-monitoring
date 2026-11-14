"""Inspect train.csv using only Python's standard library; never edits the source."""
import argparse
import csv
import json
import math
from collections import Counter
from datetime import date
from pathlib import Path

EXPECTED = {"ID", "date", "meals_served", "kitchen_staff", "temperature_C", "humidity_percent", "day_of_week", "special_event", "past_waste_kg", "staff_experience", "waste_category", "food_waste_kg"}
NUMERIC = {"ID", "meals_served", "kitchen_staff", "temperature_C", "humidity_percent", "day_of_week", "special_event", "past_waste_kg", "food_waste_kg"}


def inspect(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames or []
        rows = list(reader)
    missing = {c: sum(not (r.get(c) or "").strip() or r[c].strip().lower() == "nan" for r in rows) for c in columns}
    ranges, invalid_numeric = {}, {}
    for column in NUMERIC & set(columns):
        values, invalid = [], 0
        for row in rows:
            try:
                value = float(row[column])
                if not math.isfinite(value):
                    raise ValueError
                values.append(value)
            except (ValueError, TypeError):
                invalid += 1
        invalid_numeric[column] = invalid
        ranges[column] = {"min": min(values) if values else None, "max": max(values) if values else None}
    bad_dates = 0
    for row in rows:
        try:
            date.fromisoformat(row.get("date", ""))
        except (ValueError, TypeError):
            bad_dates += 1
    exact_duplicates = len(rows) - len({tuple(sorted(row.items())) for row in rows})
    return {"file": str(path), "row_count": len(rows), "column_count": len(columns), "columns": columns,
            "column_types": {column: "string (CSV text)" for column in columns},
            "logical_types": {"ID": "integer", "date": "date", "meals_served": "integer", "kitchen_staff": "integer",
                              "temperature_C": "float", "humidity_percent": "float", "day_of_week": "integer",
                              "special_event": "integer/flag", "past_waste_kg": "float", "staff_experience": "category",
                              "waste_category": "category", "food_waste_kg": "float"},
            "missing_or_nan": missing, "invalid_numeric_values": invalid_numeric, "numeric_ranges": ranges,
            "invalid_dates": bad_dates, "exact_duplicate_rows": exact_duplicates,
            "duplicate_IDs": len(rows) - len({r.get("ID") for r in rows}),
            "categorical_values": {c: dict(Counter(r.get(c, "") for r in rows)) for c in ("waste_category", "staff_experience") if c in columns},
            "expected_columns_present": EXPECTED.issubset(columns)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", nargs="?", default="train.csv")
    print(json.dumps(inspect(Path(parser.parse_args().csv_path)), indent=2))
