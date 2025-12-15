import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="BLS Labor Dashboard", layout="wide")

st.title("BLS Labor Dashboard (Auto-Updating)")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("data/labor_timeseries.csv", parse_dates=["date"])
    # Sort once, use everywhere
    df = df.sort_values(["series_id", "date"]).reset_index(drop=True)
    return df

df = load_data()

last_date = df["date"].max()
st.caption(f"Last data month in file: {last_date.date()}")

# Summary metrics for latest month
latest = df[df["date"] == last_date]

# Make sure we keep a stable order
metric_order = [
    "Total Nonfarm Employment (thousands)",
    "Average Hourly Earnings, Private ($)",
    "Labor Force Participation Rate (%)",
    "Employment-Population Ratio (%)",
    "Unemployment Rate (%)",
]

latest_display = (
    latest.set_index("series_name")
    .reindex(metric_order)
    .reset_index()
    .dropna(subset=["value"])
)

cols = st.columns(len(latest_display))
for col, (_, row) in zip(cols, latest_display.iterrows()):
    value_str = f"{row['value']:.1f}" if row["value"] < 1000 else f"{row['value']:.0f}"
    col.metric(row["series_name"], value_str)

st.write("")

# Main interactive line chart
st.subheader("Level of Each Series")

series_names = df["series_name"].drop_duplicates().tolist()
default_selection = series_names[:3]

selected_series = st.multiselect(
    "Choose series",
    options=series_names,
    default=default_selection,
)

if not selected_series:
    st.info("Select at least one series to see the chart.")
else:
    plot_df = df[df["series_name"].isin(selected_series)]

    level_chart = (
        alt.Chart(plot_df)
        .mark_line()
        .encode(
            x="date:T",
            y="value:Q",
            color="series_name:N",
            tooltip=[
                alt.Tooltip("series_name:N", title="Series"),
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("value:Q", title="Value"),
            ],
        )
        .properties(height=400)
    )

    st.altair_chart(level_chart, use_container_width=True)

# Month over month change
st.subheader("Month over Month Change (percent)")

# Work on a sorted copy
df_sorted = df.sort_values(["series_id", "date"]).reset_index(drop=True)
df_sorted["mom_change"] = (
    df_sorted.groupby("series_id")["value"].pct_change() * 100.0
)

if selected_series:
    mom_df = df_sorted[df_sorted["series_name"].isin(selected_series)].dropna(
        subset=["mom_change"]
    )

    mom_chart = (
        alt.Chart(mom_df)
        .mark_line()
        .encode(
            x="date:T",
            y="mom_change:Q",
            color="series_name:N",
            tooltip=[
                alt.Tooltip("series_name:N", title="Series"),
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("mom_change:Q", title="MoM change (%)", format=".2f"),
            ],
        )
        .properties(height=300)
    )

    st.altair_chart(mom_chart, use_container_width=True)
else:
    st.info("Select at least one series above to see month over month changes.")

# Year over year change
st.subheader("Year over Year Change (percent)")

df_sorted["yoy_change"] = (
    df_sorted.groupby("series_id")["value"].pct_change(12) * 100.0
)

if selected_series:
    yoy_df = df_sorted[df_sorted["series_name"].isin(selected_series)].dropna(
        subset=["yoy_change"]
    )

    yoy_chart = (
        alt.Chart(yoy_df)
        .mark_line()
        .encode(
            x="date:T",
            y="yoy_change:Q",
            color="series_name:N",
            tooltip=[
                alt.Tooltip("series_name:N", title="Series"),
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("yoy_change:Q", title="YoY change (%)", format=".2f"),
            ],
        )
        .properties(height=300)
    )

    st.altair_chart(yoy_chart, use_container_width=True)
else:
    st.info("Select at least one series above to see year over year changes.")

# Small trend panels for each selected series
st.subheader("Mini Trends for Selected Series")

if selected_series:
    # last 24 months for a simple small panel
    trend_cols = st.columns(min(len(selected_series), 3))

    for i, series in enumerate(selected_series):
        sub_df = (
            df_sorted[df_sorted["series_name"] == series]
            .sort_values("date")
            .tail(24)
        )

        small_chart = (
            alt.Chart(sub_df)
            .mark_line()
            .encode(
                x="date:T",
                y="value:Q",
            )
            .properties(height=120)
        )

        trend_cols[i % len(trend_cols)].write(f"**{series}**")
        trend_cols[i % len(trend_cols)].altair_chart(
            small_chart, use_container_width=True
        )
else:
    st.info("Select at least one series above to see mini trend panels.")
    
# Data table
st.subheader("Data")

st.dataframe(
    df.sort_values(["series_name", "date"]).reset_index(drop=True),
    use_container_width=True,
)
