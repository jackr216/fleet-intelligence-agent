"""
Week 1 — Vehicle Maintenance Ingestion
Reads Fleet_Maintenance_Output_Anon.xlsx and loads two tables into fleet.db:
  - maintenance_vehicles: full schedule for all 715 vehicles
  - maintenance_branch:   per-branch risk summary
"""

import re
import sqlite3
import pandas as pd
from config import MAINTENANCE_FILE, DB_PATH


def _clean_bool(series: pd.Series) -> pd.Series:
    """Convert Yes/No strings to 1/0 integers."""
    return series.map({"Yes": 1, "No": 0}).fillna(0).astype(int)


def _ingest_vehicles(conn: sqlite3.Connection) -> int:
    df = pd.read_excel(MAINTENANCE_FILE, sheet_name="Maintenance Schedule", header=0)
    df = df.dropna(subset=["Registration"])

    # Normalise boolean columns
    for col in ["Brakes Overdue", "Tyres Overdue", "MOT Due 30 Days", "MOT Overdue"]:
        df[col] = _clean_bool(df[col])

    # Days Since Last Repair: "No record" → None
    df["Days Since Last Repair"] = pd.to_numeric(
        df["Days Since Last Repair"].replace("No record", None), errors="coerce"
    )

    # Next MOT Date: keep as string (mixed types / NaN)
    df["Next MOT Date"] = df["Next MOT Date"].astype(str).replace("NaT", None).replace("nan", None)

    df.columns = [
        re.sub(r"[^a-zA-Z0-9_]", "_", str(c)).lower().strip("_")
        for c in df.columns
    ]

    df.to_sql("maintenance_vehicles", conn, if_exists="replace", index=False)
    return len(df)


def _ingest_branch_summary(conn: sqlite3.Connection) -> int:
    df = pd.read_excel(MAINTENANCE_FILE, sheet_name="Branch Summary", header=1)
    df = df.dropna(subset=["Branch"])

    # Rename % High Risk before normalising to avoid collision with High Risk
    df = df.rename(columns={"% High Risk": "pct_high_risk"})

    df.columns = [
        re.sub(r"[^a-zA-Z0-9_]", "_", str(c)).lower().strip("_")
        for c in df.columns
    ]

    df.to_sql("maintenance_branch", conn, if_exists="replace", index=False)
    return len(df)


def ingest():
    print(f"Ingesting vehicle maintenance from {MAINTENANCE_FILE.name}...")
    conn = sqlite3.connect(DB_PATH)

    v = _ingest_vehicles(conn)
    print(f"  maintenance_vehicles: {v} rows")

    b = _ingest_branch_summary(conn)
    print(f"  maintenance_branch:   {b} rows")

    conn.close()
    print("  Done.")


if __name__ == "__main__":
    ingest()
