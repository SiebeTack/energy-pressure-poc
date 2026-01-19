import numpy as np
import pandas as pd
from app.services.cities import CITIES, BASE_LOAD, DEFAULT_BASE

def _base_for_city(city: str) -> float:
    return float(BASE_LOAD.get(city, DEFAULT_BASE))

def iter_fake_hourly_rows(
    start="2015-01-01",
    end="2024-12-31",
    seed=42,
    batch_size=100_000,
):
    """
    Yields batches of tuples (ts, city, consumption_mwh) for efficient SQLite ingest.
    Total rows ~ (hours * cities). For 10y hourly & 50 cities ≈ 4.38M rows.
    """
    rng = np.random.default_rng(seed)
    ts_index = pd.date_range(start=start, end=end, freq="H", inclusive="both")

    # Precompute time features once (vectorized)
    hours = ts_index.hour.to_numpy()
    weekdays = ts_index.weekday.to_numpy()
    day_of_year = ts_index.dayofyear.to_numpy()

    # Patterns (vectorized)
    daily = 1.0 + 0.10 * np.sin(2 * np.pi * (hours - 7) / 24) + 0.06 * np.sin(4 * np.pi * (hours - 17) / 24)
    weekly = np.where(weekdays >= 5, 0.92, 1.0)
    seasonal = 1.0 + 0.18 * np.cos(2 * np.pi * (day_of_year / 365.25))

    # Mild long-term growth across whole series
    trend = 1.0 + (np.arange(len(ts_index)) * 0.000002)

    # Timestamp strings once
    ts_str = ts_index.strftime("%Y-%m-%dT%H:%M:%S").to_numpy()

    batch = []
    for city in CITIES:
        base = _base_for_city(city)

        noise = rng.normal(0, 0.03, size=len(ts_index))
        values = base * daily * weekly * seasonal * trend * (1 + noise)

        # rare peaks (vectorized)
        peak_mask = rng.random(len(ts_index)) < 0.002
        if peak_mask.any():
            values[peak_mask] *= rng.uniform(1.10, 1.30, size=peak_mask.sum())

        values = np.round(values.astype(float), 3)

        for t, v in zip(ts_str, values):
            batch.append((t, city, float(v)))
            if len(batch) >= batch_size:
                yield batch
                batch = []

    if batch:
        yield batch
