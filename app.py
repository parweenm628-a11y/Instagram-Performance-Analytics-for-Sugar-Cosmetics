import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="SUGAR Cosmetics Instagram Analytics",
    page_icon="💄",
    layout="wide"
)

ACCENT = "#E83E8C"


@st.cache_data
def load_data(uploaded_file=None):
    """Load the bundled Excel file or a user-uploaded Excel file."""
    if uploaded_file is not None:
        return pd.read_excel(uploaded_file)

    data_path = Path(__file__).parent / "sugar_cosmetics_instagram_data.xlsx"
    if data_path.exists():
        return pd.read_excel(data_path)

    return None


def prepare_data(data):
    df = data.copy()

    required_columns = [
        "Post Date", "Post Type", "Campaign Type", "Hashtags",
        "Audience Emotion", "Engagement Source", "Impressions", "Reach",
        "Likes", "Comments", "Shares", "Saves", "Profile Visits", "Follows"
    ]
    missing_columns = [column for column in required_columns if column not in df.columns]

    if missing_columns:
        st.error(
            "The Excel file is missing these required columns: "
            + ", ".join(missing_columns)
        )
        st.stop()

    df["Post Date"] = pd.to_datetime(df["Post Date"], errors="coerce")

    numeric_columns = [
        "Impressions", "Reach", "Likes", "Comments", "Shares",
        "Saves", "Profile Visits", "Follows"
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    categorical_columns = [
        "Post Type", "Campaign Type", "Hashtags",
        "Audience Emotion", "Engagement Source"
    ]
    for column in categorical_columns:
        df[column] = df[column].fillna("Unknown").astype(str)

    df = df.dropna(subset=["Post Date"]).copy()

    df["Total Engagement"] = df[["Likes", "Comments", "Shares", "Saves"]].sum(axis=1)
    df["Engagement Rate (%)"] = (
        df["Total Engagement"] / df["Reach"].where(df["Reach"] > 0) * 100
    )
    df["Month"] = df["Post Date"].dt.to_period("M").astype(str)
    df["Day of Week"] = df["Post Date"].dt.day_name()

    return df


st.title("💄 SUGAR Cosmetics | Instagram Performance Analytics")
st.write(
    "An interactive dashboard to explore content performance, campaigns, "
    "engagement, posting trends, hashtags, and audience actions."
)

with st.sidebar:
    st.header("Upload / Select Data")
    uploaded_file = st.file_uploader(
        "Upload the Excel dataset (.xlsx)", type=["xlsx"]
    )

raw_data = load_data(uploaded_file)

if raw_data is None:
    st.warning(
        "Dataset file not found. Upload sugar_cosmetics_instagram_data.xlsx "
        "using the sidebar."
    )
    st.stop()

df = prepare_data(raw_data)

if df.empty:
    st.warning("No rows with valid Post Date values were found.")
    st.stop()

with st.sidebar:
    st.header("Dashboard Filters")

    min_date = df["Post Date"].min().date()
    max_date = df["Post Date"].max().date()
    date_selection = st.date_input(
        "Post date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_selection, (tuple, list)) and len(date_selection) == 2:
        start_date, end_date = date_selection
    else:
        start_date, end_date = min_date, max_date

    post_type_options = sorted(df["Post Type"].unique())
    campaign_options = sorted(df["Campaign Type"].unique())
    source_options = sorted(df["Engagement Source"].unique())
    emotion_options = sorted(df["Audience Emotion"].unique())
    hashtag_options = sorted(df["Hashtags"].unique())

    selected_post_types = st.multiselect(
        "Post type", post_type_options, default=post_type_options
    )
    selected_campaigns = st.multiselect(
        "Campaign type", campaign_options, default=campaign_options
    )
    selected_sources = st.multiselect(
        "Engagement source", source_options, default=source_options
    )
    selected_emotions = st.multiselect(
        "Audience emotion", emotion_options, default=emotion_options
    )
    selected_hashtags = st.multiselect("Hashtag group", hashtag_options)

filtered = df[
    (df["Post Date"].dt.date >= start_date)
    & (df["Post Date"].dt.date <= end_date)
    & (df["Post Type"].isin(selected_post_types))
    & (df["Campaign Type"].isin(selected_campaigns))
    & (df["Engagement Source"].isin(selected_sources))
    & (df["Audience Emotion"].isin(selected_emotions))
].copy()

if selected_hashtags:
    filtered = filtered[filtered["Hashtags"].isin(selected_hashtags)]

if filtered.empty:
    st.warning("No records match the selected filters. Please change the filters.")
    st.stop()

total_engagement = int(filtered["Total Engagement"].sum())
average_rate = filtered["Engagement Rate (%)"].mean()

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Records", f"{len(filtered):,}")
k2.metric("Impressions", f"{filtered['Impressions'].sum():,.0f}")
k3.metric("Summed reach", f"{filtered['Reach'].sum():,.0f}")
k4.metric("Likes", f"{filtered['Likes'].sum():,.0f}")
k5.metric("Total interactions", f"{total_engagement:,.0f}")
k6.metric(
    "Average engagement rate",
    f"{average_rate:.2f}%" if pd.notna(average_rate) else "N/A"
)

st.caption(
    "Engagement rate = (Likes + Comments + Shares + Saves) / Reach × 100, "
    "calculated per record. Summed reach may count the same account more than once. "
    "The workbook has no unique post ID, so rows are labelled records rather than "
    "verified unique Instagram posts."
)

overview, content, timing, audience, quality = st.tabs([
    "Overview",
    "Content & Campaigns",
    "Timing Trends",
    "Hashtags & Audience",
    "Data Quality"
])

with overview:
    left, right = st.columns(2)

    monthly = filtered.groupby("Month", as_index=False).agg(
        Records=("Post Date", "size"),
        AverageEngagementRate=("Engagement Rate (%)", "mean")
    )

    with left:
        fig = px.line(
            monthly, x="Month", y="Records", markers=True,
            title="Records by Month",
            labels={"Month": "Month", "Records": "Number of records"}
        )
        fig.update_traces(line_color=ACCENT)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        type_performance = filtered.groupby("Post Type", as_index=False).agg(
            AverageLikes=("Likes", "mean"),
            AverageComments=("Comments", "mean"),
            AverageSaves=("Saves", "mean")
        )
        chart_data = type_performance.melt(
            id_vars="Post Type",
            value_vars=["AverageLikes", "AverageComments", "AverageSaves"],
            var_name="Metric",
            value_name="Average"
        )
        fig = px.bar(
            chart_data, x="Post Type", y="Average", color="Metric",
            barmode="group", title="Average interactions by content type"
        )
        st.plotly_chart(fig, use_container_width=True)

    weekday_order = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday"
    ]
    weekday = filtered.groupby("Day of Week", as_index=False)[
        "Engagement Rate (%)"
    ].mean()
    weekday["Day of Week"] = pd.Categorical(
        weekday["Day of Week"], categories=weekday_order, ordered=True
    )
    weekday = weekday.sort_values("Day of Week")

    fig = px.bar(
        weekday, x="Day of Week", y="Engagement Rate (%)",
        title="Average engagement rate by weekday"
    )
    fig.update_traces(marker_color=ACCENT)
    st.plotly_chart(fig, use_container_width=True)

with content:
    st.subheader("Content type performance")
    performance = filtered.groupby("Post Type", as_index=False).agg(
        Records=("Post Type", "size"),
        AverageLikes=("Likes", "mean"),
        AverageComments=("Comments", "mean"),
        AverageShares=("Shares", "mean"),
        AverageSaves=("Saves", "mean"),
        AverageReach=("Reach", "mean"),
        AverageEngagementRate=("Engagement Rate (%)", "mean")
    )
    st.dataframe(performance, use_container_width=True)

    campaign = filtered.groupby("Campaign Type", as_index=False).agg(
        Records=("Campaign Type", "size"),
        AverageEngagementRate=("Engagement Rate (%)", "mean"),
        AverageLikes=("Likes", "mean"),
        AverageReach=("Reach", "mean"),
        TotalFollows=("Follows", "sum")
    )
    fig = px.bar(
        campaign.sort_values("AverageEngagementRate", ascending=False),
        x="Campaign Type", y="AverageEngagementRate",
        color="Campaign Type", title="Average engagement rate by campaign"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 10 records by likes")
    st.dataframe(
        filtered.nlargest(10, "Likes")[
            ["Post Date", "Post Type", "Campaign Type", "Likes",
             "Comments", "Shares", "Saves", "Reach", "Hashtags"]
        ],
        use_container_width=True
    )

    st.subheader("Top 10 records by engagement rate")
    st.dataframe(
        filtered.dropna(subset=["Engagement Rate (%)"]).nlargest(
            10, "Engagement Rate (%)"
        )[
            ["Post Date", "Post Type", "Campaign Type", "Total Engagement",
             "Reach", "Engagement Rate (%)", "Hashtags"]
        ],
        use_container_width=True
    )

with timing:
    monthly_trend = filtered.groupby("Month", as_index=False).agg(
        Records=("Post Date", "size"),
        AverageEngagementRate=("Engagement Rate (%)", "mean"),
        TotalLikes=("Likes", "sum"),
        TotalFollows=("Follows", "sum"),
        TotalProfileVisits=("Profile Visits", "sum")
    )

    left, right = st.columns(2)
    with left:
        fig = px.line(
            monthly_trend, x="Month", y="AverageEngagementRate",
            markers=True, title="Average engagement rate by month"
        )
        fig.update_traces(line_color=ACCENT)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.bar(
            monthly_trend, x="Month", y="TotalFollows",
            title="Recorded follows by month"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(monthly_trend, use_container_width=True)

with audience:
    left, right = st.columns(2)

    hashtag_summary = filtered.groupby("Hashtags", as_index=False).agg(
        Records=("Hashtags", "size"),
        AverageEngagementRate=("Engagement Rate (%)", "mean"),
        AverageReach=("Reach", "mean"),
        AverageLikes=("Likes", "mean")
    )
    hashtag_summary = hashtag_summary[hashtag_summary["Records"] >= 30]
    hashtag_summary = hashtag_summary.nlargest(15, "AverageEngagementRate")

    with left:
        if not hashtag_summary.empty:
            fig = px.bar(
                hashtag_summary.sort_values("AverageEngagementRate"),
                x="AverageEngagementRate", y="Hashtags",
                orientation="h", title="Top hashtag groups by engagement rate",
                hover_data=["Records", "AverageReach", "AverageLikes"]
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough hashtag groups have 30 or more records.")

    source_summary = filtered.groupby("Engagement Source", as_index=False).agg(
        Records=("Engagement Source", "size"),
        AverageEngagementRate=("Engagement Rate (%)", "mean")
    )
    with right:
        fig = px.bar(
            source_summary, x="Engagement Source",
            y="AverageEngagementRate", color="Engagement Source",
            title="Average engagement rate by source"
        )
        st.plotly_chart(fig, use_container_width=True)

    emotion_summary = filtered.groupby("Audience Emotion", as_index=False).agg(
        Records=("Audience Emotion", "size"),
        AverageEngagementRate=("Engagement Rate (%)", "mean")
    )
    fig = px.bar(
        emotion_summary, x="Audience Emotion",
        y="AverageEngagementRate", color="Audience Emotion",
        title="Average engagement rate by audience emotion"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Hashtags are stored as groups/combinations in this dataset. "
        "The analysis compares those groups and does not isolate individual hashtag effects."
    )

with quality:
    st.subheader("Data quality checks")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows loaded", f"{len(raw_data):,}")
    c2.metric("Columns", f"{len(raw_data.columns):,}")
    c3.metric("Exact duplicate rows", f"{int(raw_data.duplicated().sum()):,}")
    c4.metric("Missing cells", f"{int(raw_data.isna().sum().sum()):,}")

    quality_table = pd.DataFrame({
        "Column": raw_data.columns,
        "Data type": [str(dtype) for dtype in raw_data.dtypes],
        "Missing values": [int(raw_data[column].isna().sum()) for column in raw_data.columns],
        "Distinct values": [int(raw_data[column].nunique(dropna=True)) for column in raw_data.columns]
    })
    st.dataframe(quality_table, use_container_width=True)

st.divider()
st.subheader("Insights for the current filter selection")

type_rates = filtered.groupby("Post Type")["Engagement Rate (%)"].mean().dropna().sort_values(ascending=False)
day_rates = filtered.groupby("Day of Week")["Engagement Rate (%)"].mean().dropna().sort_values(ascending=False)
campaign_rates = filtered.groupby("Campaign Type")["Engagement Rate (%)"].mean().dropna().sort_values(ascending=False)

if not type_rates.empty:
    st.write(
        f"**Content type:** {type_rates.index[0]} has the highest average engagement "
        f"rate in the selected data ({type_rates.iloc[0]:.2f}%)."
    )
if not day_rates.empty:
    st.write(
        f"**Weekday:** {day_rates.index[0]} has the highest average engagement "
        f"rate in the selected data ({day_rates.iloc[0]:.2f}%). Treat this as a "
        "candidate for testing, not proof of causation."
    )
if not campaign_rates.empty:
    st.write(
        f"**Campaign:** {campaign_rates.index[0]} has the highest average engagement "
        f"rate in the selected data ({campaign_rates.iloc[0]:.2f}%)."
    )

if total_engagement > 0:
    likes_share = filtered["Likes"].sum() / total_engagement * 100
    st.write(f"**Interaction mix:** Likes represent {likes_share:.1f}% of recorded interactions.")

st.caption(
    "Confirm what each row represents and validate the data source before making "
    "strong claims about the official Instagram account."
)
