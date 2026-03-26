import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DB_PATH = DATA_DIR / "fleet.db"

# --- Raw data files ---
FUEL_FILE = RAW_DIR / "Fuel_Forecast_Outout_Anon.xlsx"
MAINTENANCE_FILE = RAW_DIR / "Fleet_Maintenance_Output_Anon.xlsx"
CVR_FILE = RAW_DIR / "CVR_Exceptions_Output_Anon.xlsx"

# --- Claude API ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-opus-4-6"

# --- Agent settings ---
MAX_TOOL_ITERATIONS = 10
