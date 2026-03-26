# Fleet Intelligence Agent

A multi-model agentic AI system that orchestrates three ML model outputs — Fuel Forecasting, Vehicle Maintenance Risk, and CVR Exception Detection — to produce unified, cross-domain fleet intelligence via a conversational AI interface.

---

## Project Overview

Rather than a static dashboard, this system uses Claude's tool-calling API to dynamically query the right data, reason across all three models, and return prioritised natural language recommendations with supporting evidence.

**Key capabilities:**
- Ask open-ended questions about fleet health and get evidence-based answers
- Cross-model alerts: vehicles or branches flagged across multiple models simultaneously
- Branch health scoring combining operational risk, financial exposure, and exception rates
- Per-vehicle intelligence combining fuel cost forecast and maintenance risk profile
- Weekly briefing generation: automated natural language fleet health summaries

---

## Architecture

```
User Question
     │
     ▼
Agent (Claude API + tool-calling)
     │
     ├── get_fleet_summary()
     ├── get_vehicle_profile(reg)
     ├── get_branch_health(branch)
     ├── get_fuel_forecast(...)
     ├── find_high_risk_vehicles(...)
     └── find_cross_model_alerts()
          │
          ▼
     SQLite (fleet.db)
          │
     ┌────┴────────────┐
  Fuel DB    Maintenance DB    CVR DB
```

---

## Data Sources

| Model | File | Link Key |
|---|---|---|
| Fuel Forecast | `Fuel_Forecast_Output_Anon.xlsx` | Registration, Branch |
| Vehicle Maintenance | `Fleet_Maintenance_Output_Anon.xlsx` | Registration, Branch |
| CVR Exceptions | `CVR_Exceptions_Output_Anon.xlsx` | Branch |

- 629 vehicles shared between Fuel + Maintenance datasets
- 37 branches across all three datasets

---

## Project Structure

```
Multi_Model_Agent/
├── data/
│   ├── raw/                    # Source Excel files (3 model outputs)
│   ├── processed/              # Cleaned CSVs (intermediate)
│   └── fleet.db                # SQLite database (generated)
├── ingestion/
│   ├── schema.sql              # Database schema
│   ├── ingest_fuel.py          # Fuel forecast ingestion
│   ├── ingest_maintenance.py   # Maintenance risk ingestion
│   └── ingest_cvr.py           # CVR exception ingestion
├── agent/
│   ├── tools.py                # Tool functions (called by Claude)
│   ├── orchestrator.py         # Agent loop + Claude API integration
│   └── prompts.py              # System prompts
├── api/
│   ├── main.py                 # FastAPI application
│   └── routes.py               # API endpoints
├── frontend/
│   ├── index.html              # Fleet dashboard
│   ├── chat.html               # Chat interface
│   └── static/                 # CSS, JS assets
├── config.py                   # Configuration + paths
├── requirements.txt
└── .env                        # API keys (not committed)
```

---

## Setup

### 1. Clone & install dependencies

```bash
cd Multi_Model_Agent
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Ingest data

```bash
py -m ingestion.ingest_fuel
py -m ingestion.ingest_maintenance
py -m ingestion.ingest_cvr
```

Or run all at once:

```bash
py -c "from ingestion.ingest_fuel import ingest; from ingestion.ingest_maintenance import ingest as ingest2; from ingestion.ingest_cvr import ingest as ingest3; ingest(); ingest2(); ingest3()"
```

### 4. Start the API

```bash
py -m uvicorn api.main:app --reload
```

### 5. Open the dashboard

Navigate to `http://localhost:8000` in your browser.

---

## Example Agent Interactions

**Branch triage:**
> "Which branches need the most urgent attention right now?"

**Vehicle deep dive:**
> "Tell me everything about Reg_0289"

**Cost-risk correlation:**
> "Are our highest fuel-cost vehicles also our highest risk?"

**Weekly briefing:**
> "Give me a fleet health summary for this week"

---

## Tech Stack

| Component | Technology |
|---|---|
| AI / Agent | Claude API (tool-calling) |
| Database | SQLite |
| Backend | FastAPI + Uvicorn |
| Frontend | HTML / JS / Chart.js |
| Data processing | Pandas + openpyxl |
| Environment | Python 3.10+ |

---

## Development Roadmap

- [x] Week 1 — Data ingestion layer
- [ ] Week 2 — Agent core + tool-use (CLI demo)
- [ ] Week 3 — FastAPI + basic dashboard
- [ ] Week 4 — Chat interface + cross-model intelligence
- [ ] Week 5 — Polish, documentation, GitHub

---

## Portfolio Notes

This project demonstrates:
- LLM tool-use / function-calling (agentic patterns)
- Multi-source data integration (ETL pipelines, SQLite)
- Full-stack AI product development (FastAPI + frontend)
- Cross-domain reasoning across ML model outputs
