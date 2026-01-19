from app.core.db import get_conn, init_db


def get_cities_from_db() -> list[str]:
    """
    Returns the list of cities currently present in the database.
    We take them from hourly_consumption (most complete),
    and fall back to monthly_consumption if needed.
    """
    init_db()

    with get_conn() as conn:
        # Prefer hourly (raw) if available
        row = conn.execute("SELECT COUNT(*) AS n FROM hourly_consumption;").fetchone()
        hourly_n = int(row["n"]) if row else 0

        if hourly_n > 0:
            rows = conn.execute("SELECT DISTINCT city FROM hourly_consumption ORDER BY city ASC;").fetchall()
            return [r["city"] for r in rows]

        # Fallback to aggregates (region column contains city names)
        rows = conn.execute("SELECT DISTINCT region FROM monthly_consumption ORDER BY region ASC;").fetchall()
        return [r["region"] for r in rows]
