import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="BLS Labor Dashboard", layout="wide")
st.title("BLS Labor Dashboard (Auto-Updating)")

df = pd.read_csv("data/labor_timeseries.csv", parse_dates=["date"])
latest_date = df["date"].max()
st.caption(f"Last data month in file: {latest_date.date()}")

# Show simple “latest value” cards for core series
core = df[df["series_id"].isin([
    "CES0000000001", "LNS14000000", "LNS11300000", "LNS12300000", "CES0500000003"
])]
latest = core[core["date"] == latest_date].sort_values("series_id")

col1, col2, col3, col4, col5 = st.columns(5)
cols = [col1, col2, col3, col4, col5]
for col, (_, row) in zip(cols, latest.iterrows()):
    col.metric(row["series_name"], f"{row['value']}")

# Interactive line chart
series_names = df["series_name"].drop_duplicates().tolist()
pick = st.multiselect("Choose series", series_names, default=series_names[:3])

plot_df = df[df["series_name"].isin(pick)]
line = alt.Chart(plot_df).mark_line().encode(
    x="date:T",
    y="value:Q",
    color="series_name:N",
    tooltip=["series_name", alt.Tooltip("date:T", title="Date"), alt.Tooltip("value:Q", title="Value")]
).properties(height=400)
st.altair_chart(line, use_container_width=True)

st.subheader("Data")
st.dataframe(plot_df.sort_values(["series_name", "date"]))
