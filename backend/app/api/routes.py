from fastapi import APIRouter

from app.services.ingest import ingest_fake_data
from app.services.query import get_monthly, get_daily
from app.services.trends import monthly_with_trends
from app.services.forecasting_baseline import forecast_monthly_baseline
from app.services.forecasting_ml import forecast_monthly_ml
from app.services.meta import get_cities_from_db
from app.services.ingest import ingest_fake_hourly_cities

router = APIRouter()

# --- Health ---
@router.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

# --- Ingest ---
@router.post("/ingest/fake", tags=["ingest"])
def ingest_fake(start: str = "2021-01-01", end: str = "2024-12-31", seed: int = 42):
    return ingest_fake_data(start=start, end=end, seed=seed)

@router.post("/ingest/fake-hourly-cities", tags=["ingest"])
def ingest_fake_hourly_cities_endpoint(start: str = "2015-01-01", end: str = "2024-12-31", seed: int = 42):
    return ingest_fake_hourly_cities(start=start, end=end, seed=seed)

# --- Consumption ---
@router.get("/consumption/monthly", tags=["consumption"])
def consumption_monthly(region: str | None = None):
    return get_monthly(region=region)

@router.get("/consumption/daily", tags=["consumption"])
def consumption_daily(region: str | None = None, start: str | None = None, end: str | None = None):
    return get_daily(region=region, start=start, end=end)

# --- Trends ---
@router.get("/trends/monthly", tags=["trends"])
def trends_monthly(region: str | None = None, window: int = 3, peak_q: float = 0.90):
    return monthly_with_trends(region=region, window=window, peak_q=peak_q)

# --- Forecast ---
@router.get("/forecast/baseline", tags=["forecast"])
def forecast_baseline(region: str, periods: int = 6):
    return forecast_monthly_baseline(region=region, periods=periods)

@router.get("/forecast/ml", tags=["forecast"])
def forecast_ml(region: str, periods: int = 6):
    return forecast_monthly_ml(region=region, periods=periods)

@router.get("/meta/cities", tags=["meta"])
def meta_cities():
    return {"cities": get_cities_from_db()}