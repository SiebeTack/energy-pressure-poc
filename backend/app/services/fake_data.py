import numpy as np
import pandas as pd

REGIONS = ["Flanders", "Wallonia", "Brussels"]

def generate_fake_consumption(
    start: str = "2021-01-01",
    end: str = "2024-12-31",
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate daily electricity consumption (MWh) per region.
    Includes: seasonality, weekly pattern, long-term trend, and random peaks.
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start, end=end, freq="D")

    rows = []
    for region in REGIONS:
        base = {"Flanders": 32000, "Wallonia": 21000, "Brussels": 9000}[region]
        trend_per_day = {"Flanders": 2.0, "Wallonia": 1.2, "Brussels": 0.6}[region]

        for i, d in enumerate(dates):
            day_of_year = d.timetuple().tm_yday
            weekday = d.weekday()

            # Seasonality: winter higher, summer lower
            seasonal = 1.0 + 0.18 * np.cos(2 * np.pi * (day_of_year / 365.25))

            # Weekly: weekends lower
            weekly = 0.92 if weekday >= 5 else 1.0

            # Trend
            trend = 1.0 + (trend_per_day * i) / base

            # Noise
            noise = rng.normal(0, 0.03)

            value = base * seasonal * weekly * trend * (1 + noise)

            # Random peaks (rare)
            if rng.random() < 0.015:
                value *= rng.uniform(1.10, 1.25)

            rows.append(
                {
                    "date": d.date().isoformat(),
                    "region": region,
                    "consumption_mwh": round(float(value), 2),
                }
            )

    return pd.DataFrame(rows)
