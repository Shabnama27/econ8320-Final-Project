import os
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

# where to save the data
DATA_PATH = Path("data/labor_timeseries.csv")

# BLS API info
BLS_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# series id -> readable name
SERIES = {
    "CES0000000001": "Total Nonfarm Employment (thousands)",  # payroll employment
    "LNS14000000": "Unemployment Rate (%)",
    "LNS11300000": "Labor Force Participation Rate (%)",
    "LNS12300000": "Employment-Population Ratio (%)",
    "CES0500000003": "Avg Hourly Earnings, Private ($)",
}

# how far back to pull data
START_YEAR = 2010


def fetch_series(series_id: str, start_year: int) -> pd.DataFrame:
    """Fetch one BLS series and return a tidy DataFrame."""
    end_year = datetime.today().year

    # API key from environment (set this in GitHub Secrets for Actions)
    api_key = os.getenv("BLS_API_KEY")

    payload = {
        "seriesid": [series_id],
        "startyear": start_year,
        "endyear": end_year,
    }
    if api_key:
        payload["registrationkey"] = api_key

    resp = requests.post(BLS_URL, json=payload)
    resp.raise_for_status()
    json_data = resp.json()

    series_list = json_data["Results"]["series"][0]["data"]

    rows = []
    for item in series_list:
        year = int(item["year"])
        period = item["period"]  # "M01", "M02", ..., "M13"
        value = float(item["value"])

        # skip annual "M13" values
        if not period.startswith("M"):
            continue
        month_num = int(period[1:])
        if month_num == 13:
            continue

        date = datetime(year, month_num, 1)

        rows.append(
            {
                "series_id": series_id,
                "series_name": SERIES.get(series_id, series_id),
                "date": date,
                "value": value,
            }
        )

    df = pd.DataFrame(rows)
    return df


def main():
    # fetch all series and stack them together
    all_dfs = []
    for sid in SERIES.keys():
        print(f"Fetching {sid} ...")
        df_sid = fetch_series(sid, START_YEAR)
        all_dfs.append(df_sid)

    new_data = pd.concat(all_dfs, ignore_index=True)

    # if file exists, read it and append, otherwise start fresh
    if DATA_PATH.exists():
        print("Existing CSV found, merging with new data.")
        old_data = pd.read_csv(DATA_PATH, parse_dates=["date"])
        combined = pd.concat([old_data, new_data], ignore_index=True)
    else:
        print("No existing CSV, creating a new one.")
        combined = new_data

    # drop duplicates (same series + date) and sort
    combined = (
        combined.drop_duplicates(subset=["series_id", "date"])
        .sort_values(["series_id", "date"])
        .reset_index(drop=True)
    )

    # make sure folder exists
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    combined.to_csv(DATA_PATH, index=False)
    print(f"Saved {len(combined)} rows to {DATA_PATH}")


if __name__ == "__main__":
    main()
