import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor

from app.core.db import get_conn, init_db

def forecast_monthly_ml(region: str, periods: int = 6) -> list[dict]:
    """
    ML forecast using Random Forest with lag features.
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
    if df.empty or len(df) < 12:
        return []

    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values("month")

    # Feature engineering
    df["lag_1"] = df["consumption_mwh"].shift(1)
    df["lag_3"] = df["consumption_mwh"].shift(3)
    df["month_num"] = df["month"].dt.month

    df = df.dropna()

    X = df[["lag_1", "lag_3", "month_num"]]
    y = df["consumption_mwh"]

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42
    )
    model.fit(X, y)

    last = df.iloc[-1]
    preds = []

    lag1 = last["consumption_mwh"]
    lag3 = df.iloc[-3]["consumption_mwh"]

    current_month = last["month"]

    for i in range(periods):
        current_month = current_month + pd.offsets.MonthBegin(1)

        X_next = pd.DataFrame([{
            "lag_1": lag1,
            "lag_3": lag3,
            "month_num": current_month.month,
        }])

        yhat = model.predict(X_next)[0]
        preds.append((current_month, yhat))

        lag3 = lag1
        lag1 = yhat

    now = datetime.utcnow().isoformat()

    return [
        {
            "model": "ml_random_forest",
            "region": region,
            "month": m.strftime("%Y-%m"),
            "yhat": round(float(y), 2),
            "created_at": now,
        }
        for m, y in preds
    ]
