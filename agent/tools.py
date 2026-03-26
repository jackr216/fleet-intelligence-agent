"""
Week 2 — Agent Tools
Functions the Claude agent can call via tool-use.
Each function queries fleet.db and returns structured data.
"""

import sqlite3
from config import DB_PATH


def _query(sql: str, params: tuple = ()) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _query_one(sql: str, params: tuple = ()) -> dict | None:
    results = _query(sql, params)
    return results[0] if results else None


# --- Tool: Fleet summary ---
def get_fleet_summary() -> dict:
    """Top-level fleet KPIs across all three models."""
    maintenance = _query_one("""
        SELECT
            COUNT(*) AS total_vehicles,
            SUM(CASE WHEN risk_band = 'High' THEN 1 ELSE 0 END) AS high_risk,
            SUM(CASE WHEN risk_band = 'Medium' THEN 1 ELSE 0 END) AS medium_risk,
            SUM(CASE WHEN risk_band = 'Low' THEN 1 ELSE 0 END) AS low_risk,
            SUM(brakes_overdue) AS brakes_overdue,
            SUM(tyres_overdue) AS tyres_overdue,
            SUM(mot_overdue) AS mot_overdue,
            SUM(mot_due_30_days) AS mot_due_30_days
        FROM maintenance_vehicles
    """)

    fuel = _query_one("SELECT SUM(total_spend) AS total_fuel_forecast FROM fuel_vehicle")

    cvr = _query_one("""
        SELECT
            COUNT(DISTINCT branch) AS branches_with_exceptions,
            COUNT(*) AS total_flagged_jobs,
            ROUND(AVG(risk_score), 2) AS avg_cvr_risk_score
        FROM cvr_flagged_jobs
        WHERE month = 'February 2026'
    """)

    branch_count = _query_one("SELECT COUNT(DISTINCT branch) AS total_branches FROM maintenance_branch")

    return {
        "total_vehicles": maintenance["total_vehicles"],
        "total_branches": branch_count["total_branches"],
        "risk_distribution": {
            "high": maintenance["high_risk"],
            "medium": maintenance["medium_risk"],
            "low": maintenance["low_risk"],
        },
        "maintenance_flags": {
            "brakes_overdue": maintenance["brakes_overdue"],
            "tyres_overdue": maintenance["tyres_overdue"],
            "mot_overdue": maintenance["mot_overdue"],
            "mot_due_30_days": maintenance["mot_due_30_days"],
        },
        "fuel_total_forecast_gbp": fuel["total_fuel_forecast"],
        "cvr_latest_month": {
            "branches_with_exceptions": cvr["branches_with_exceptions"],
            "total_flagged_jobs": cvr["total_flagged_jobs"],
            "avg_risk_score": cvr["avg_cvr_risk_score"],
        },
    }


# --- Tool: Vehicle profile ---
def get_vehicle_profile(registration: str) -> dict | None:
    """Full cross-model profile for a single vehicle (fuel + maintenance)."""
    row = _query_one(
        "SELECT * FROM vehicle_profile WHERE UPPER(registration) = UPPER(?)",
        (registration,),
    )
    return row


# --- Tool: Branch health ---
def get_branch_health(branch: str) -> dict | None:
    """Aggregated health score for a branch across all three models."""
    row = _query_one(
        "SELECT * FROM branch_health WHERE UPPER(branch) = UPPER(?)",
        (branch,),
    )
    if not row:
        return None

    # Full CVR monthly breakdown (all 3 months)
    cvr_monthly = _query_one(
        "SELECT * FROM cvr_branch_summary WHERE UPPER(branch) = UPPER(?)",
        (branch,),
    )
    if cvr_monthly:
        row.update(cvr_monthly)

    # Flagged jobs ranked by severity (risk score desc, then wip excess desc)
    flagged_jobs = _query("""
        SELECT job_no, month, risk_score, total_wip, wip_excess,
               wip___turnover AS wip_to_turnover_ratio, monthly_turnover, exception
        FROM cvr_flagged_jobs
        WHERE UPPER(branch) = UPPER(?)
        ORDER BY risk_score DESC, wip_excess DESC
    """, (branch,))
    row["flagged_jobs"] = flagged_jobs

    # Top high-risk vehicles for this branch
    top_vehicles = _query("""
        SELECT registration, make, model, risk_score, brakes_overdue,
               tyres_overdue, recommended_action
        FROM maintenance_vehicles
        WHERE UPPER(branch) = UPPER(?)
        ORDER BY risk_score DESC
        LIMIT 5
    """, (branch,))
    row["top_risk_vehicles"] = top_vehicles

    return row


# --- Tool: Fuel forecast ---
def get_fuel_forecast(top_n: int = 20, branch: str = None) -> list[dict]:
    """Returns vehicles ranked by forecasted fuel spend. Optionally filter by branch."""
    if branch:
        return _query(
            "SELECT registration, branch, make, model, total_spend FROM fuel_vehicle "
            "WHERE UPPER(branch) = UPPER(?) ORDER BY total_spend DESC LIMIT ?",
            (branch, top_n),
        )
    return _query(
        "SELECT registration, branch, make, model, total_spend FROM fuel_vehicle "
        "ORDER BY total_spend DESC LIMIT ?",
        (top_n,),
    )


# --- Tool: High risk vehicles ---
def find_high_risk_vehicles(branch: str = None, limit: int = 20) -> list[dict]:
    """Returns vehicles with the highest maintenance risk scores."""
    if branch:
        return _query("""
            SELECT registration, branch, make, model, risk_band, risk_score,
                   brakes_overdue, tyres_overdue, mot_overdue, recommended_action
            FROM maintenance_vehicles
            WHERE risk_band = 'High' AND UPPER(branch) = UPPER(?)
            ORDER BY risk_score DESC
            LIMIT ?
        """, (branch, limit))
    return _query("""
        SELECT registration, branch, make, model, risk_band, risk_score,
               brakes_overdue, tyres_overdue, mot_overdue, recommended_action
        FROM maintenance_vehicles
        WHERE risk_band = 'High'
        ORDER BY risk_score DESC
        LIMIT ?
    """, (limit,))


# --- Tool: Cross-model alerts ---
def find_cross_model_alerts() -> dict:
    """Finds vehicles and branches flagged as high-risk across multiple models simultaneously."""

    # Branches: high maintenance risk AND active CVR exceptions
    high_risk_branches = _query("""
        SELECT
            bh.branch,
            bh.pct_high_risk,
            bh.high_risk AS high_risk_vehicles,
            bh.total_vans,
            bh.fuel_total_spend,
            bh.cvr_avg_risk_score,
            bh.cvr_latest_flagged,
            bh.cvr_latest_pct_flagged
        FROM branch_health bh
        WHERE bh.pct_high_risk >= 30
          AND bh.cvr_avg_risk_score IS NOT NULL
        ORDER BY (bh.pct_high_risk + COALESCE(bh.cvr_avg_risk_score, 0)) DESC
        LIMIT 10
    """)

    # Vehicles: high maintenance risk AND in top fuel spenders
    dual_risk_vehicles = _query("""
        SELECT
            vp.registration,
            vp.branch,
            vp.make,
            vp.model,
            vp.risk_score,
            vp.risk_band,
            vp.brakes_overdue,
            vp.tyres_overdue,
            vp.fuel_total_spend,
            vp.recommended_action
        FROM vehicle_profile vp
        WHERE vp.risk_band = 'High'
          AND vp.fuel_total_spend IS NOT NULL
        ORDER BY vp.risk_score DESC, vp.fuel_total_spend DESC
        LIMIT 15
    """)

    return {
        "multi_signal_branches": high_risk_branches,
        "high_risk_high_cost_vehicles": dual_risk_vehicles,
    }


# --- Tool definitions for Claude API ---
TOOL_DEFINITIONS = [
    {
        "name": "get_fleet_summary",
        "description": "Get top-level fleet KPIs: total vehicles, branch count, risk distribution, maintenance flags, forecast fuel spend, and CVR exception summary. Call this first for broad overview questions.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_vehicle_profile",
        "description": "Get the full cross-model profile for a single vehicle: maintenance risk score, overdue flags, MOT status, driver score, and fuel cost forecast.",
        "input_schema": {
            "type": "object",
            "properties": {
                "registration": {"type": "string", "description": "Vehicle registration identifier, e.g. Reg_0289"}
            },
            "required": ["registration"],
        },
    },
    {
        "name": "get_branch_health",
        "description": "Get the aggregated health score for a specific branch across all three models: maintenance risk breakdown, fuel forecast spend, CVR exception rate, and top high-risk vehicles.",
        "input_schema": {
            "type": "object",
            "properties": {
                "branch": {"type": "string", "description": "Branch identifier, e.g. Branch_05"}
            },
            "required": ["branch"],
        },
    },
    {
        "name": "get_fuel_forecast",
        "description": "Get vehicles ranked by forecasted annual fuel spend (April 2026 – March 2027). Optionally filter by branch.",
        "input_schema": {
            "type": "object",
            "properties": {
                "top_n": {"type": "integer", "description": "Number of vehicles to return (default 20)"},
                "branch": {"type": "string", "description": "Optional branch filter"},
            },
            "required": [],
        },
    },
    {
        "name": "find_high_risk_vehicles",
        "description": "Get vehicles rated High risk by the maintenance model, ordered by risk score. Optionally filter by branch.",
        "input_schema": {
            "type": "object",
            "properties": {
                "branch": {"type": "string", "description": "Optional branch filter"},
                "limit": {"type": "integer", "description": "Max vehicles to return (default 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "find_cross_model_alerts",
        "description": "Find vehicles and branches flagged as high-risk across multiple models simultaneously. Returns branches with both high maintenance risk and CVR exceptions, plus vehicles that are both high maintenance risk and high fuel cost.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]
