import sqlite3
from pathlib import Path


# DB file: backend/storage/energy.sqlite
DB_PATH = Path(__file__).resolve().parents[2] / "storage" / "energy.sqlite"


def get_conn() -> sqlite3.Connection:
    """
    Returns a SQLite connection with Row factory enabled.
    Ensures the storage folder exists.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Creates all tables + indexes if they don't exist.
    We store:
      - hourly raw data (for better forecasts/features)
      - daily & monthly aggregates (fast queries/dashboard)
      - monthly forecasts (optional storage)
    """
    with get_conn() as conn:
        # --- Hourly raw (cities) ---
        conn.execute("""
        CREATE TABLE IF NOT EXISTS hourly_consumption (
            ts TEXT NOT NULL,              -- ISO timestamp: YYYY-MM-DDTHH:MM:SS
            city TEXT NOT NULL,
            consumption_mwh REAL NOT NULL,
            PRIMARY KEY (ts, city)
        );
        """)

        # --- Daily aggregates (we keep column name 'region' but it will contain city names) ---
        conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_consumption (
            date TEXT NOT NULL,            -- YYYY-MM-DD
            region TEXT NOT NULL,          -- city name
            consumption_mwh REAL NOT NULL,
            PRIMARY KEY (date, region)
        );
        """)

        # --- Monthly aggregates ---
        conn.execute("""
        CREATE TABLE IF NOT EXISTS monthly_consumption (
            month TEXT NOT NULL,           -- YYYY-MM
            region TEXT NOT NULL,          -- city name
            consumption_mwh REAL NOT NULL,
            PRIMARY KEY (month, region)
        );
        """)

        # --- Forecast storage (monthly) ---
        conn.execute("""
        CREATE TABLE IF NOT EXISTS forecast_monthly (
            model TEXT NOT NULL,           -- e.g. "baseline", "ml_random_forest"
            month TEXT NOT NULL,           -- YYYY-MM
            region TEXT NOT NULL,          -- city name
            yhat REAL NOT NULL,
            created_at TEXT NOT NULL,      -- ISO timestamp
            PRIMARY KEY (model, month, region)
        );
        """)

        # --- Indexes for performance ---
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hourly_city_ts ON hourly_consumption(city, ts);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_region_date ON daily_consumption(region, date);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_monthly_region_month ON monthly_consumption(region, month);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_forecast_region_month ON forecast_monthly(region, month);")
