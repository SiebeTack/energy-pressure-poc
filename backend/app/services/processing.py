import pandas as pd

def to_monthly(df_daily: pd.DataFrame) -> pd.DataFrame:
    df = df_daily.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    monthly = (
        df.groupby(["month", "region"], as_index=False)["consumption_mwh"]
        .sum()
        .rename(columns={"consumption_mwh": "consumption_mwh"})
    )
    monthly["consumption_mwh"] = monthly["consumption_mwh"].round(2)
    return monthly
