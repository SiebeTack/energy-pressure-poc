import streamlit as st
import pandas as pd
import requests
import plotly.express as px

API = "http://127.0.0.1:8000"

st.title("Energy Pressure Dashboard (POC)")

# Health check
try:
    r = requests.get(f"{API}/health", timeout=2)
    st.success(f"Backend OK: {r.json()}")
except Exception as e:
    st.error(f"Backend not reachable: {e}")
    st.stop()

# Fetch cities dynamically
try:
    cities_resp = requests.get(f"{API}/meta/cities", timeout=10).json()
    cities = cities_resp.get("cities", [])
    if not cities:
        st.warning("No cities found in DB. Run POST /ingest/fake-hourly-cities first.")
        st.stop()
except Exception as e:
    st.error(f"Could not load cities from backend: {e}")
    st.stop()

st.divider()

city = st.selectbox("City", cities)
periods = st.slider("Forecast months ahead", min_value=3, max_value=12, value=6)

# Historical monthly data
hist = requests.get(f"{API}/consumption/monthly", params={"region": city}, timeout=10).json()
df_hist = pd.DataFrame(hist)
df_hist["month"] = pd.to_datetime(df_hist["month"])
df_hist = df_hist.sort_values("month")
df_hist["series"] = "historical"

# Forecasts
base = requests.get(f"{API}/forecast/baseline", params={"region": city, "periods": periods}, timeout=10).json()
ml = requests.get(f"{API}/forecast/ml", params={"region": city, "periods": periods}, timeout=10).json()

frames = [df_hist[["month", "consumption_mwh", "series"]]]

df_base = pd.DataFrame(base)
if not df_base.empty:
    df_base["month"] = pd.to_datetime(df_base["month"])
    df_base["series"] = "baseline"
    df_base = df_base.rename(columns={"yhat": "consumption_mwh"})
    frames.append(df_base[["month", "consumption_mwh", "series"]])

df_ml = pd.DataFrame(ml)
if not df_ml.empty:
    df_ml["month"] = pd.to_datetime(df_ml["month"])
    df_ml["series"] = "ml_random_forest"
    df_ml = df_ml.rename(columns={"yhat": "consumption_mwh"})
    frames.append(df_ml[["month", "consumption_mwh", "series"]])

df_all = pd.concat(frames, ignore_index=True).sort_values("month")

st.subheader("Historical + Forecast comparison")
fig = px.line(df_all, x="month", y="consumption_mwh", color="series", markers=True)
st.plotly_chart(fig, use_container_width=True)

show_hourly = st.checkbox("Show hourly forecast (next 24h)", value=True)

if show_hourly:
    resp = requests.get(
        f"{API}/forecast/hourly",
        params={"city": city, "horizon": 24, "lookback_days": 730},
        timeout=30
    ).json()

    if "error" in resp:
        st.error(resp["error"])
    else:
        df_hist = pd.DataFrame(resp["history"])
        df_hist["ts"] = pd.to_datetime(df_hist["ts"])
        df_hist = df_hist.rename(columns={"consumption_mwh": "value"})
        df_hist["series"] = "history"

        df_fc = pd.DataFrame(resp["forecast"])
        df_fc["ts"] = pd.to_datetime(df_fc["ts"])
        df_fc = df_fc.rename(columns={"yhat": "value"})
        df_fc["series"] = "forecast_24h"

        df_all = pd.concat([df_hist, df_fc], ignore_index=True).sort_values("ts")

        st.subheader("Hourly forecast (last 7 days + next 24h)")
        fig = px.line(df_all, x="ts", y="value", color="series", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        st.caption(f"Validation MAE (last slice): {resp['metrics'].get('mae_validation'):.2f} MWh")

