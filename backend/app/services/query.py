import pandas as pd
from app.core.db import get_conn, init_db

def get_monthly(region: str | None = None) -> list[dict]:
    init_db()
    q = "SELECT month, region, consumption_mwh FROM monthly_consumption"
    params = []
    if region:
        q += " WHERE region = ?"
        params.append(region)
    q += " ORDER BY month ASC, region ASC;"

    with get_conn() as conn:
        rows = conn.execute(q, params).fetchall()
    return [dict(r) for r in rows]

def get_daily(region: str | None = None, start: str | None = None, end: str | None = None) -> list[dict]:
    init_db()
    q = "SELECT date, region, consumption_mwh FROM daily_consumption WHERE 1=1"
    params = []
    if region:
        q += " AND region = ?"
        params.append(region)
    if start:
        q += " AND date >= ?"
        params.append(start)
    if end:
        q += " AND date <= ?"
        params.append(end)
    q += " ORDER BY date ASC, region ASC;"

    with get_conn() as conn:
        rows = conn.execute(q, params).fetchall()
    return [dict(r) for r in rows]
