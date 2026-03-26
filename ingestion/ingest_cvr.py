"""
Week 1 — CVR Exceptions Ingestion
Reads CVR_Exceptions_Output_Anon.xlsx and loads two tables into fleet.db:
  - cvr_flagged_jobs:   per-job flagged rows with WIP/turnover figures
  - cvr_branch_summary: per-branch exception counts + avg risk score across 3 months
"""

import re
import sqlite3
import pandas as pd
from config import CVR_FILE, DB_PATH


def _ingest_flagged_jobs(conn: sqlite3.Connection) -> int:
    df = pd.read_excel(CVR_FILE, sheet_name="Flagged Jobs", header=0)
    df = df.dropna(subset=["Branch"])

    df.columns = [
        re.sub(r"[^a-zA-Z0-9_]", "_", str(c)).lower().strip("_")
        for c in df.columns
    ]

    df.to_sql("cvr_flagged_jobs", conn, if_exists="replace", index=False)
    return len(df)


def _ingest_branch_summary(conn: sqlite3.Connection) -> int:
    """
    Branch Breakdown sheet has a two-row header:
    Row 0: Branch | December 2025 | ... | January 2026 | ... | February 2026 | ... | Avg Risk Score
    Row 1: Branch | Total Jobs | Flagged | % Flagged | Total Jobs | Flagged | % Flagged | ...

    We flatten this into explicit column names.
    """
    df = pd.read_excel(CVR_FILE, sheet_name="Branch Breakdown", header=None)

    # Build explicit column names from the two header rows
    months = ["dec_2025", "jan_2026", "feb_2026"]
    cols = ["branch"]
    for m in months:
        cols += [f"{m}_total_jobs", f"{m}_flagged", f"{m}_pct_flagged"]
    cols.append("avg_risk_score")

    # Data starts at row 2
    data = df.iloc[2:].copy()
    data.columns = cols
    data = data.dropna(subset=["branch"])
    data = data.reset_index(drop=True)

    # Coerce numeric columns
    for col in cols[1:]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data.to_sql("cvr_branch_summary", conn, if_exists="replace", index=False)
    return len(data)


def ingest():
    print(f"Ingesting CVR exceptions from {CVR_FILE.name}...")
    conn = sqlite3.connect(DB_PATH)

    j = _ingest_flagged_jobs(conn)
    print(f"  cvr_flagged_jobs:    {j} rows")

    b = _ingest_branch_summary(conn)
    print(f"  cvr_branch_summary:  {b} rows")

    conn.close()
    print("  Done.")


if __name__ == "__main__":
    ingest()
