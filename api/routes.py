"""
Week 3 — API Routes
"""

import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import DB_PATH
from agent.tools import get_fleet_summary, get_vehicle_profile, get_branch_health
from agent.orchestrator import ask

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


# --- Chat ---

@router.post("/api/chat")
def chat(req: ChatRequest):
    answer = ask(req.message)
    return {"response": answer}


# --- Fleet ---

@router.get("/api/fleet/summary")
def fleet_summary():
    return get_fleet_summary()


# --- Branches ---

@router.get("/api/branches")
def list_branches():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT * FROM branch_health
        ORDER BY pct_high_risk DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/api/branch/{branch_id}")
def branch_detail(branch_id: str):
    data = get_branch_health(branch_id)
    if not data:
        raise HTTPException(status_code=404, detail="Branch not found")
    return data


# --- Vehicles ---

@router.get("/api/vehicle/{registration}")
def vehicle_detail(registration: str):
    data = get_vehicle_profile(registration)
    if not data:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Attach monthly fuel forecast
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    fuel = conn.execute(
        "SELECT * FROM fuel_vehicle WHERE UPPER(registration) = UPPER(?)",
        (registration,)
    ).fetchone()
    conn.close()

    if fuel:
        monthly_cols = ['2026_04','2026_05','2026_06','2026_07','2026_08','2026_09',
                        '2026_10','2026_11','2026_12','2027_01','2027_02','2027_03']
        data["monthly_fuel"] = {c: fuel[c] for c in monthly_cols if fuel[c] is not None}

    return data
