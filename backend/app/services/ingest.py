from __future__ import annotations

from datetime import datetime, timezone
import time

from app.core.db import get_conn, init_db
from app.services.fake_data import generate_fake_consumption
from app.services.processing import to_monthly
from app.services.fake_data_hourly_cities import iter_fake_hourly_rows


def ingest_fake_data(start: str = "2021-01-01", end: str = "2024-12-31", seed: int = 42) -> dict:
    """
    Simple (daily) ingest:
      - generate daily synthetic data (region = "Flanders/Wallonia/Brussels")
      - store daily + monthly aggregates in SQLite
      - does NOT store any raw files
    """
    init_db()

    df_daily = generate_fake_consumption(start=start, end=end, seed=seed)
    df_monthly = to_monthly(df_daily)

    with get_conn() as conn:
        # POC simplicity: full rebuild
        conn.execute("DELETE FROM daily_consumption;")
        conn.execute("DELETE FROM monthly_consumption;")

        conn.executemany(
            "INSERT INTO daily_consumption(date, region, consumption_mwh) VALUES (?, ?, ?);",
            df_daily[["date", "region", "consumption_mwh"]].itertuples(index=False, name=None),
        )

        conn.executemany(
            "INSERT INTO monthly_consumption(month, region, consumption_mwh) VALUES (?, ?, ?);",
            df_monthly[["month", "region", "consumption_mwh"]].itertuples(index=False, name=None),
        )

    return {
        "status": "ingested",
        "daily_rows": int(len(df_daily)),
        "monthly_rows": int(len(df_monthly)),
        "range": {"start": start, "end": end},
        "seed": seed,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def ingest_fake_hourly_cities(start: str = "2015-01-01", end: str = "2024-12-31", seed: int = 42) -> dict:
    """
    High-volume ingest (hourly, 50 cities, 10 years):
      - generates synthetic hourly rows in chunks (generator)
      - stores hourly data in SQLite (hourly_consumption)
      - rebuilds daily_consumption and monthly_consumption using SQL aggregation
    """
    init_db()
    t0 = time.perf_counter()

    total_rows = 0

    with get_conn() as conn:
        # Speed pragmas for faster bulk ingest
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA temp_store=MEMORY;")

        # Fresh load (POC)
        conn.execute("DELETE FROM hourly_consumption;")

        # Chunked bulk insert
        for batch in iter_fake_hourly_rows(start=start, end=end, seed=seed, batch_size=120_000):
            conn.executemany(
                "INSERT INTO hourly_consumption(ts, city, consumption_mwh) VALUES (?, ?, ?);",
                batch,
            )
            total_rows += len(batch)

        # Rebuild aggregates in SQL (fast and memory-friendly)
        conn.execute("DELETE FROM daily_consumption;")
        conn.execute("""
            INSERT INTO daily_consumption(date, region, consumption_mwh)
            SELECT substr(ts, 1, 10) AS date,
                   city AS region,
                   ROUND(SUM(consumption_mwh), 2) AS consumption_mwh
            FROM hourly_consumption
            GROUP BY date, city;
        """)

        conn.execute("DELETE FROM monthly_consumption;")
        conn.execute("""
            INSERT INTO monthly_consumption(month, region, consumption_mwh)
            SELECT substr(ts, 1, 7) AS month,
                   city AS region,
                   ROUND(SUM(consumption_mwh), 2) AS consumption_mwh
            FROM hourly_consumption
            GROUP BY month, city;
        """)

    t1 = time.perf_counter()
    seconds = t1 - t0

    return {
        "status": "ingested_hourly_cities",
        "hourly_rows": int(total_rows),
        "rows_per_sec": round(total_rows / seconds, 2) if seconds > 0 else None,
        "seconds": round(seconds, 2),
        "range": {"start": start, "end": end},
        "seed": seed,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
