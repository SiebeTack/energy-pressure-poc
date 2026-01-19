import pandas as pd
from datetime import datetime
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from app.core.db import get_conn, init_db

def forecast_monthly_baseline(region: str, periods: int = 6) -> list[dict]:
    """
    Forecast monthly consumption using exponential smoothing.
    """
    init_db()

    q = """
    SELECT month, consumption_mwh
    FROM monthly_consumption
    WHERE region = ?
    ORDER BY month ASC;
    """

    with get_conn() as conn:
        rows = conn.execute(q, (region,)).fetchall()

    df = pd.DataFrame([dict(r) for r in rows])
    if df.empty or len(df) < 6:
        return []

    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values("month")

    model = ExponentialSmoothing(
        df["consumption_mwh"],
        trend="add",
        seasonal="add",
        seasonal_periods=12
    )
    fit = model.fit()

    forecast = fit.forecast(periods)

    last_month = df["month"].iloc[-1]
    future_months = pd.date_range(
        start=last_month + pd.offsets.MonthBegin(1),
        periods=periods,
        freq="MS"
    )

    now = datetime.utcnow().isoformat()

    return [
        {
            "model": "baseline",
            "region": region,
            "month": m.strftime("%Y-%m"),
            "yhat": round(float(y), 2),
            "created_at": now,
        }
        for m, y in zip(future_months, forecast)
    ]
