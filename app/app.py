import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="BLS Labor Dashboard", layout="wide")
st.title("BLS Labor Dashboard")

# load data once and reuse it
@st.cache_data
def load_data():
    df = pd.read_csv("data/labor_timeseries.csv", parse_dates=["date"])
    df = df.sort_values(["series_id", "date"]).reset_index(drop=True)
    return df

full_df = load_data()

# show last date in the data
last_date = full_df["date"].max()
st.caption(f"Last data month in file: {last_date.date()}")

# choose year range for charts
years = full_df["date"].dt.year
min_year = int(years.min())
max_year = int(years.max())

st.subheader("Select time range for charts")
start_year, end_year = st.slider(
    "Year range",
    min_value=min_year,
    max_value=max_year,
    value=(max(min_year, max_year - 2), max_year),  # default is last 3 years
)

start_date = pd.Timestamp(start_year, 1, 1)
end_date = pd.Timestamp(end_year, 12, 31)

# filter data for charts
df = full_df[(full_df["date"] >= start_date) & (full_df["date"] <= end_date)].copy()

# show latest values as metrics (use full data, not filtered)
latest_df = full_df[full_df["date"] == last_date]

metric_order = [
    "Total Nonfarm Employment (thousands)",
    "Average Hourly Earnings, Private ($)",
    "Labor Force Participation Rate (%)",
    "Employment-Population Ratio (%)",
    "Unemployment Rate (%))",
]

latest_df = (
    latest_df.set_index("series_name")
    .reindex(metric_order)
    .reset_index()
    .dropna(subset=["value"])
)

cols = st.columns(len(latest_df))
for col, (_, row) in zip(cols, latest_df.iterrows()):
    if row["value"] < 1000:
        value_str = f"{row['value']:.1f}"
    else:
        value_str = f"{row['value']:.0f}"
    col.metric(row["series_name"], value_str)

st.write("")

# main line chart
st.subheader("Level of each series")

if df.empty:
    st.warning("No data in this year range. Try a different range.")
else:
    series_list = sorted(df["series_name"].unique().tolist())
    default_series = series_list[:3]

    selected = st.multiselect(
        "Choose series to plot",
        options=series_list,
        default=default_series,
    )

    if len(selected) == 0:
        st.info("Select at least one series to see the line chart.")
    else:
        df_plot = df[df["series_name"].isin(selected)]

        line_chart = (
            alt.Chart(df_plot)
            .mark_line()
            .encode(
                x="date:T",
                y="value:Q",
                color="series_name:N",
                tooltip=["series_name", "date:T", "value:Q"],
            )
            .properties(height=400)
        )
        st.altair_chart(line_chart, use_container_width=True)

# month over month change
st.subheader("Month over month change (percent)")

df_range_sorted = df.sort_values(["series_id", "date"]).reset_index(drop=True)
df_range_sorted["mom_change"] = (
    df_range_sorted.groupby("series_id")["value"].pct_change() * 100
)

if df.empty or len(selected) == 0:
    st.info("Select at least one series above to see month over month changes.")
else:
    mom_df = df_range_sorted[
        df_range_sorted["series_name"].isin(selected)
    ].dropna(subset=["mom_change"])

    mom_chart = (
        alt.Chart(mom_df)
        .mark_line()
        .encode(
            x="date:T",
            y="mom_change:Q",
            color="series_name:N",
            tooltip=[
                "series_name",
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("mom_change:Q", title="MoM change (%)", format=".2f"),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(mom_chart, use_container_width=True)

# year over year change
st.subheader("Year over year change (percent)")

full_sorted = full_df.sort_values(["series_id", "date"]).reset_index(drop=True)
full_sorted["yoy_change"] = (
    full_sorted.groupby("series_id")["value"].pct_change(12) * 100
)

yoy_range_df = full_sorted[
    (full_sorted["date"] >= start_date) & (full_sorted["date"] <= end_date)
]

if df.empty or len(selected) == 0:
    st.info("Select at least one series above to see year over year changes.")
else:
    yoy_df = yoy_range_df[
        yoy_range_df["series_name"].isin(selected)
    ].dropna(subset=["yoy_change"])

    yoy_chart = (
        alt.Chart(yoy_df)
        .mark_line()
        .encode(
            x="date:T",
            y="yoy_change:Q",
            color="series_name:N",
            tooltip=[
                "series_name",
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("yoy_change:Q", title="YoY change (%)", format=".2f"),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(yoy_chart, use_container_width=True)

# mini trend panels
st.subheader("Mini trends (by series)")

if df.empty or len(selected) == 0:
    st.info("Select at least one series above to see mini trends.")
else:
    n_cols = min(len(selected), 3)
    trend_cols = st.columns(n_cols)

    for i, name in enumerate(selected):
        df_one = df[df["series_name"] == name].sort_values("date")

        mini_chart = (
            alt.Chart(df_one)
            .mark_line()
            .encode(
                x="date:T",
                y="value:Q",
            )
            .properties(height=120)
        )

        col_idx = i % n_cols
        trend_cols[col_idx].write(f"**{name}**")
        trend_cols[col_idx].altair_chart(mini_chart, use_container_width=True)

# data table
st.subheader("Data for selected year range")

df_table = df.sort_values(["series_name", "date"]).reset_index(drop=True)
st.dataframe(df_table, use_container_width=True)
