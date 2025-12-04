import os, json, requests, pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

SERIES = [
    ("CES0000000001", "Total Nonfarm Employment (thous)"),
    ("LNS14000000", "Unemployment Rate (%)"),
    ("LNS11300000", "Labor Force Participation Rate (%)"),
    ("LNS12300000", "Employment-Population Ratio (%)"),
    ("CES0500000003", "Avg Hourly Earnings, Private ($)")
]

API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
API_KEY = os.getenv("BLS_API_KEY")  # put this in a GitHub Secret later

# last 24 months for a clean start
end = datetime.today().date().replace(day=1)
start = (end - relativedelta(months=24))

payload = {
    "seriesid": [s[0] for s in SERIES],
    "startyear": str(start.year),
    "endyear": str(end.year),
}
if API_KEY:
    payload["registrationkey"] = API_KEY

r = requests.post(API_URL, json=payload, timeout=60)
r.raise_for_status()
resp = r.json()
if resp.get("status") != "REQUEST_SUCCEEDED":
    raise SystemExit(json.dumps(resp, indent=2))

rows = []
for series in resp["Results"]["series"]:
    sid = series["seriesID"]
    name = dict(SERIES)[sid]
    for item in series["data"]:
        # BLS period "M01"... "M12"; skip "M13" (annual)
        if not item["period"].startswith("M"):
            continue
        year = int(item["year"])
        month = int(item["period"][1:])
        value = float(item["value"])
        date = pd.Timestamp(year=year, month=month, day=1)
        rows.append({
            "series_id": sid,
            "series_name": name,
            "date": date,
            "value": value
        })

df = pd.DataFrame(rows)
df = df.sort_values(["series_id", "date"]).reset_index(drop=True)

# Append-only: if a file exists, keep old rows and add new ones
out_path = "data/labor_timeseries.csv"
if os.path.exists(out_path):
    old = pd.read_csv(out_path, parse_dates=["date"])
    df = pd.concat([old, df], ignore_index=True).drop_duplicates(
        subset=["series_id", "date"], keep="last"
    )

df.to_csv(out_path, index=False)
print(f"Saved {len(df)} rows to {out_path}")
