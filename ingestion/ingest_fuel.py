"""
Week 1 — Fuel Forecast Ingestion
Reads Fuel_Forecast_Outout_Anon.xlsx and loads two tables into fleet.db:
  - fuel_vehicle: per-vehicle monthly spend forecast + totals
  - fuel_branch:  per-branch monthly spend forecast + totals
"""

import re
import sqlite3
import pandas as pd
from config import FUEL_FILE, DB_PATH

MONTHLY_COLS = [
    "2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09",
    "2026-10", "2026-11", "2026-12", "2027-01", "2027-02", "2027-03",
]


def _strip_currency(series: pd.Series) -> pd.Series:
    """Remove £ signs and commas, convert to float."""
    return (
        series.astype(str)
        .str.replace(r"[£,]", "", regex=True)
        .str.strip()
        .replace("nan", None)
        .pipe(pd.to_numeric, errors="coerce")
    )


def _ingest_vehicle_forecast(conn: sqlite3.Connection) -> int:
    df = pd.read_excel(FUEL_FILE, sheet_name="Vehicle Forecast", header=1)
    df = df.dropna(subset=["Registration"])

    # Clean currency columns
    for col in MONTHLY_COLS + ["Total Spend (£)"]:
        df[col] = _strip_currency(df[col])

    df = df.rename(columns={"Total Spend (£)": "total_spend"})

    # Normalise column names
    df.columns = [
        re.sub(r"[^a-zA-Z0-9_]", "_", str(c)).lower().strip("_")
        for c in df.columns
    ]

    df.to_sql("fuel_vehicle", conn, if_exists="replace", index=False)
    return len(df)


def _ingest_branch_forecast(conn: sqlite3.Connection) -> int:
    df = pd.read_excel(FUEL_FILE, sheet_name="Branch Forecast", header=1)
    df = df.dropna(subset=["Branch"])

    for col in MONTHLY_COLS + ["Total Spend (£)"]:
        df[col] = _strip_currency(df[col])

    df = df.rename(columns={"Total Spend (£)": "total_spend"})

    df.columns = [
        re.sub(r"[^a-zA-Z0-9_]", "_", str(c)).lower().strip("_")
        for c in df.columns
    ]

    df.to_sql("fuel_branch", conn, if_exists="replace", index=False)
    return len(df)


def ingest():
    print(f"Ingesting fuel forecast from {FUEL_FILE.name}...")
    conn = sqlite3.connect(DB_PATH)

    v = _ingest_vehicle_forecast(conn)
    print(f"  fuel_vehicle: {v} rows")

    b = _ingest_branch_forecast(conn)
    print(f"  fuel_branch:  {b} rows")

    conn.close()
    print("  Done.")


if __name__ == "__main__":
    ingest()
