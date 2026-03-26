-- Fleet Intelligence Agent — SQLite Schema
-- Tables are created via pandas to_sql; this file documents the intended structure
-- and defines the cross-model views built on top.

-- ============================================================
-- FUEL FORECAST  (source: Fuel_Forecast_Outout_Anon.xlsx)
-- ============================================================

-- fuel_vehicle: one row per vehicle, 12 monthly spend columns + total
-- registration | branch | make | model | 2026_04 ... 2027_03 | total_spend

-- fuel_branch: one row per branch, 12 monthly spend columns + total
-- branch | 2026_04 ... 2027_03 | total_spend

-- ============================================================
-- VEHICLE MAINTENANCE  (source: Fleet_Maintenance_Output_Anon.xlsx)
-- ============================================================

-- maintenance_vehicles: full schedule for all 715 vehicles
-- registration | branch | make | model | van_type | vehicle_age__yrs_
-- total_miles | driver_score | risk_band | risk_score
-- brakes_overdue | tyres_overdue | days_since_last_repair
-- next_mot_date | mot_due_30_days | mot_overdue | recommended_action

-- maintenance_branch: per-branch risk summary
-- branch | total_vans | high_risk | medium_risk | low_risk
-- brakes_overdue | tyres_overdue | mot_due_30_days | __high_risk

-- ============================================================
-- CVR EXCEPTIONS  (source: CVR_Exceptions_Output_Anon.xlsx)
-- ============================================================

-- cvr_flagged_jobs: one row per flagged job
-- month | branch | job_no_ | monthly_turnover___ | total_wip___
-- wip_excess___ | wip___turnover | risk_score | exception

-- cvr_branch_summary: per-branch exception summary across 3 months
-- branch | dec_2025_total_jobs | dec_2025_flagged | dec_2025_pct_flagged
-- jan_2026_total_jobs | jan_2026_flagged | jan_2026_pct_flagged
-- feb_2026_total_jobs | feb_2026_flagged | feb_2026_pct_flagged
-- avg_risk_score

-- ============================================================
-- CROSS-MODEL VIEWS
-- ============================================================

-- Per-vehicle view: fuel forecast + maintenance risk
CREATE VIEW IF NOT EXISTS vehicle_profile AS
SELECT
    m.registration,
    m.branch,
    m.make,
    m.model,
    m.van_type,
    m.vehicle_age__yrs        AS vehicle_age_yrs,
    m.total_miles,
    m.driver_score,
    m.risk_band,
    m.risk_score,
    m.brakes_overdue,
    m.tyres_overdue,
    m.days_since_last_repair,
    m.next_mot_date,
    m.mot_due_30_days,
    m.mot_overdue,
    m.recommended_action,
    f.total_spend              AS fuel_total_spend
FROM maintenance_vehicles m
LEFT JOIN fuel_vehicle f ON UPPER(m.registration) = UPPER(f.registration);

-- Per-branch view: fuel + maintenance + CVR combined
CREATE VIEW IF NOT EXISTS branch_health AS
SELECT
    mb.branch,
    mb.total_vans,
    mb.high_risk,
    mb.medium_risk,
    mb.low_risk,
    mb.brakes_overdue          AS maint_brakes_overdue,
    mb.tyres_overdue           AS maint_tyres_overdue,
    mb.mot_due_30_days,
    mb.pct_high_risk,
    fb.total_spend             AS fuel_total_spend,
    cvr.avg_risk_score         AS cvr_avg_risk_score,
    cvr.feb_2026_flagged       AS cvr_latest_flagged,
    cvr.feb_2026_total_jobs    AS cvr_latest_total_jobs,
    cvr.feb_2026_pct_flagged   AS cvr_latest_pct_flagged
FROM maintenance_branch mb
LEFT JOIN fuel_branch fb   ON mb.branch = fb.branch
LEFT JOIN cvr_branch_summary cvr ON mb.branch = cvr.branch;
