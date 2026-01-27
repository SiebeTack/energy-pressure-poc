from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

from app.core.db import get_conn, init_db


@dataclass
class HourlyForecastResult:
    city: str
    horizon: int
    lookback_days: int
    train_rows: int
    metrics: dict[str, Any]
    history: list[dict[str, Any]]
    forecast: list[dict[str, Any]]


def _fetch_hourly(city: str, lookback_days: int) -> pd.DataFrame:
    init_db()
    cutoff = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y-%m-%dT%H:%M:%S")

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT ts, consumption_mwh
            FROM hourly_consumption
            WHERE city = ?
              AND ts >= ?
            ORDER BY ts ASC;
            """,
            (city, cutoff),
        ).fetchall()

    if not rows:
        return pd.DataFrame(columns=["ts", "consumption_mwh"])

    df = pd.DataFrame(rows, columns=["ts", "consumption_mwh"])
    df["ts"] = pd.to_datetime(df["ts"])
    df["consumption_mwh"] = df["consumption_mwh"].astype(float)
    return df


def _add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    # Calendar/time features (no leakage)
    df = df.copy()
    df["hour"] = df["ts"].dt.hour
    df["dow"] = df["ts"].dt.dayofweek
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["month"] = df["ts"].dt.month

    # cyclic encoding
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    return df


def _make_supervised(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build supervised learning table for 1-step-ahead forecasting.
    Uses only past values (lags/rolling).
    """
    df = df.copy()
    y = df["consumption_mwh"]

    # Strong lags for hourly series
    df["lag_1"] = y.shift(1)
    df["lag_24"] = y.shift(24)
    df["lag_168"] = y.shift(168)

    # Rolling stats
    df["roll_mean_24"] = y.shift(1).rolling(24).mean()
    df["roll_std_24"] = y.shift(1).rolling(24).std()
    df["roll_mean_168"] = y.shift(1).rolling(168).mean()

    # Target = next hour
    df["target"] = y.shift(-1)

    # Drop rows with missing lags/target
    df = df.dropna().reset_index(drop=True)
    return df


def _train_model(df_sup: pd.DataFrame) -> tuple[HistGradientBoostingRegressor, dict[str, Any]]:
    feature_cols = [
        "lag_1", "lag_24", "lag_168",
        "roll_mean_24", "roll_std_24", "roll_mean_168",
        "hour_sin", "hour_cos", "month_sin", "month_cos",
        "dow", "is_weekend",
    ]

    X = df_sup[feature_cols].to_numpy()
    y = df_sup["target"].to_numpy()

    # Time-based split: last 30 days for validation if possible
    # 30 days hourly = 720 rows
    val_size = 720 if len(df_sup) > 2000 else max(1, int(len(df_sup) * 0.2))
    split = len(df_sup) - val_size

    X_train, y_train = X[:split], y[:split]
    X_val, y_val = X[split:], y[split:]

    model = HistGradientBoostingRegressor(
        max_depth=8,
        learning_rate=0.08,
        max_iter=400,
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_val)
    mae = float(mean_absolute_error(y_val, y_pred))

    metrics = {
        "mae_validation": mae,
        "train_rows": int(len(X_train)),
        "val_rows": int(len(X_val)),
    }
    return model, metrics


def _feature_row_from_history(
    ts_next: pd.Timestamp,
    history_values: list[float],
) -> dict[str, float]:
    """
    Build one feature row for ts_next using history_values ending at ts_next-1h.
    history_values[-1] = last observed/predicted hour.
    """
    # Need at least 168 hours of history for lag_168 & roll_mean_168
    if len(history_values) < 168:
        raise ValueError("Not enough history to create hourly features (need >= 168 hours).")

    lag_1 = history_values[-1]
    lag_24 = history_values[-24]
    lag_168 = history_values[-168]

    last_24 = history_values[-24:]
    last_168 = history_values[-168:]

    roll_mean_24 = float(np.mean(last_24))
    roll_std_24 = float(np.std(last_24, ddof=1)) if len(last_24) > 1 else 0.0
    roll_mean_168 = float(np.mean(last_168))

    hour = ts_next.hour
    dow = ts_next.dayofweek
    is_weekend = 1 if dow >= 5 else 0
    month = ts_next.month

    hour_sin = float(np.sin(2 * np.pi * hour / 24))
    hour_cos = float(np.cos(2 * np.pi * hour / 24))
    month_sin = float(np.sin(2 * np.pi * month / 12))
    month_cos = float(np.cos(2 * np.pi * month / 12))

    return {
        "lag_1": float(lag_1),
        "lag_24": float(lag_24),
        "lag_168": float(lag_168),
        "roll_mean_24": roll_mean_24,
        "roll_std_24": roll_std_24,
        "roll_mean_168": roll_mean_168,
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "month_sin": month_sin,
        "month_cos": month_cos,
        "dow": float(dow),
        "is_weekend": float(is_weekend),
    }


def forecast_hourly_ml(city: str, horizon: int = 24, lookback_days: int = 730) -> dict[str, Any]:
    """
    On-demand hourly forecast for one city.
    - Trains fast on last lookback_days (default 2 years)
    - Predicts next 'horizon' hours (default 24h)
    """
    if horizon < 1 or horizon > 168:
        raise ValueError("horizon must be between 1 and 168")

    df = _fetch_hourly(city=city, lookback_days=lookback_days)
    if df.empty:
        return {"error": f"No hourly data found for city '{city}'."}

    df = _add_time_features(df)
    df_sup = _make_supervised(df)

    if len(df_sup) < 2000:
        return {"error": "Not enough data for hourly ML forecast (need at least ~2000 supervised rows)."}

    model, metrics = _train_model(df_sup)

    # History for plotting: last 7 days
    hist_df = df.tail(24 * 7).copy()
    history = [
        {"ts": t.strftime("%Y-%m-%dT%H:%M:%S"), "consumption_mwh": float(v)}
        for t, v in zip(hist_df["ts"], hist_df["consumption_mwh"])
    ]

    # Recursive forecasting for next horizon hours
    # Seed history_values with the most recent values from full df
    values = df["consumption_mwh"].tolist()
    last_ts = df["ts"].iloc[-1]

    feature_cols = [
        "lag_1", "lag_24", "lag_168",
        "roll_mean_24", "roll_std_24", "roll_mean_168",
        "hour_sin", "hour_cos", "month_sin", "month_cos",
        "dow", "is_weekend",
    ]

    preds: list[dict[str, Any]] = []
    for step in range(1, horizon + 1):
        ts_next = last_ts + timedelta(hours=step)
        row = _feature_row_from_history(ts_next, values)
        X_next = np.array([[row[c] for c in feature_cols]], dtype=float)
        yhat = float(model.predict(X_next)[0])

        preds.append({"ts": ts_next.strftime("%Y-%m-%dT%H:%M:%S"), "yhat": yhat})
        values.append(yhat)  # feed prediction forward

    result = HourlyForecastResult(
        city=city,
        horizon=horizon,
        lookback_days=lookback_days,
        train_rows=int(metrics.get("train_rows", 0)),
        metrics=metrics,
        history=history,
        forecast=preds,
    )
    return {
        "city": result.city,
        "horizon": result.horizon,
        "lookback_days": result.lookback_days,
        "metrics": result.metrics,
        "history": result.history,
        "forecast": result.forecast,
    }