import pandas as pd
from app.core.db import get_conn, init_db

def monthly_with_trends(region: str | None = None, window: int = 3, peak_q: float = 0.90) -> list[dict]:
    """
    Returns monthly consumption + rolling average + peak flag + pressure label.
    peak_q = quantile threshold for peak detection (0.90 = top 10%)
    """
    init_db()

    q = "SELECT month, region, consumption_mwh FROM monthly_consumption"
    params = []
    if region:
        q += " WHERE region = ?"
        params.append(region)
    q += " ORDER BY month ASC;"

    with get_conn() as conn:
        rows = conn.execute(q, params).fetchall()

    df = pd.DataFrame([dict(r) for r in rows])
    if df.empty:
        return []

    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values(["region", "month"])

    out = []
    for reg, g in df.groupby("region"):
        g = g.copy()
        g["rolling_mean"] = g["consumption_mwh"].rolling(window=window, min_periods=1).mean()

        thresh = float(g["consumption_mwh"].quantile(peak_q))
        g["is_peak"] = g["consumption_mwh"] >= thresh

        mean = float(g["consumption_mwh"].mean())
        high = float(g["consumption_mwh"].quantile(0.90))

        def label(x: float) -> str:
            if x >= high:
                return "high"
            if x >= mean:
                return "elevated"
            return "normal"

        g["pressure"] = g["consumption_mwh"].apply(label)

        g["month"] = g["month"].dt.to_period("M").astype(str)
        g["rolling_mean"] = g["rolling_mean"].round(2)
        g["threshold_peak"] = round(thresh, 2)

        out.extend(g[["month", "region", "consumption_mwh", "rolling_mean", "is_peak", "pressure", "threshold_peak"]].to_dict("records"))

    return out
