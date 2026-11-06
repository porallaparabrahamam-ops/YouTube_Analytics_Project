import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="YouTube Analytics Dashboard",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #0B1020;
    color: #FFFFFF;
}

[data-testid="stSidebar"] {
    background-color: #11182B;
}

[data-testid="stMetric"] {
    background-color: #17233D;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #293957;
}

[data-testid="stMetricLabel"] {
    color: #AAB8D0;
}

[data-testid="stMetricValue"] {
    color: #FFFFFF;
}

h1, h2, h3 {
    color: #FFFFFF !important;
}

p {
    color: #B8C5DC;
}

div.stButton > button {
    background-color: #6655E8;
    color: white;
    border-radius: 8px;
    border: none;
}

div.stButton > button:hover {
    background-color: #8675FF;
    color: white;
}

.block-container {
    padding-top: 2rem;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# COLOR CONFIGURATION
# =====================================================

COLORS = [
    "#7667F5",
    "#06B6D4",
    "#10B981",
    "#F59E0B",
    "#EC4899",
    "#8B5CF6",
    "#EF4444"
]

CHART_TEMPLATE = "plotly_dark"


# =====================================================
# DATA LOADING
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

POSSIBLE_FILES = [
    BASE_DIR / "Dataset" / "youtube_engagement.csv",
    BASE_DIR / "Dataset" / "uploads.csv",
    BASE_DIR / "Dataset" / "INvideos.csv",
    BASE_DIR / "youtube_engagement.csv"
]


@st.cache_data
def load_data():

    for file in POSSIBLE_FILES:

        if file.exists():

            df = pd.read_csv(file)

            return df, str(file)

    return None, None


df, DATA_PATH = load_data()


if df is None:

    st.error(
        "Dataset not found. Please place "
        "youtube_engagement.csv inside the Dataset folder."
    )

    st.stop()


# =====================================================
# COLUMN STANDARDIZATION
# =====================================================

df.columns = df.columns.str.strip()

ALIASES = {

    "channel": [
        "channel",
        "channel_title",
        "channel_name"
    ],

    "category": [
        "youtube_category",
        "category",
        "category_name"
    ],

    "upload_type": [
        "upload_type",
        "content_type",
        "video_type"
    ],

    "views": [
        "views",
        "view_count",
        "total_views"
    ],

    "likes": [
        "likes",
        "like_count"
    ],

    "comments": [
        "comments",
        "comment_count",
        "comments_count"
    ],

    "engagement_rate": [
        "engagement_rate_pct",
        "engagement_rate",
        "engagement"
    ],

    "published": [
        "published_utc",
        "publish_time",
        "published_at",
        "published_date"
    ],

    "video_id": [
        "video_id",
        "id"
    ],

    "duration": [
        "seconds",
        "duration_seconds"
    ]

}


def find_column(possible_names):

    for name in possible_names:

        if name in df.columns:

            return name

    return None


COLUMN_MAP = {}

for standard_name, aliases in ALIASES.items():

    COLUMN_MAP[standard_name] = find_column(aliases)


# Required columns

required = ["channel", "views"]

missing = [
    col for col in required
    if COLUMN_MAP[col] is None
]

if missing:

    st.error(
        f"Required dataset columns are missing: {missing}"
    )

    st.write("Available columns:", list(df.columns))

    st.stop()


# =====================================================
# DATA CLEANING
# =====================================================

df["Channel"] = (
    df[COLUMN_MAP["channel"]]
    .fillna("Unknown")
    .astype(str)
)

if COLUMN_MAP["category"]:

    df["Category"] = (
        df[COLUMN_MAP["category"]]
        .fillna("Unknown")
        .astype(str)
    )

else:

    df["Category"] = "Unknown"


if COLUMN_MAP["upload_type"]:

    df["Upload Type"] = (
        df[COLUMN_MAP["upload_type"]]
        .fillna("Unknown")
        .astype(str)
    )

else:

    df["Upload Type"] = "Unknown"


df["Views"] = pd.to_numeric(
    df[COLUMN_MAP["views"]],
    errors="coerce"
).fillna(0)


if COLUMN_MAP["likes"]:

    df["Likes"] = pd.to_numeric(
        df[COLUMN_MAP["likes"]],
        errors="coerce"
    ).fillna(0)

else:

    df["Likes"] = 0


if COLUMN_MAP["comments"]:

    df["Comments"] = pd.to_numeric(
        df[COLUMN_MAP["comments"]],
        errors="coerce"
    ).fillna(0)

else:

    df["Comments"] = 0


if COLUMN_MAP["engagement_rate"]:

    df["Engagement Rate"] = pd.to_numeric(
        df[COLUMN_MAP["engagement_rate"]],
        errors="coerce"
    )

else:

    df["Engagement Rate"] = np.nan


# Calculate engagement if missing

calculated_engagement = np.where(
    df["Views"] > 0,
    (
        (df["Likes"] + df["Comments"])
        / df["Views"]
    ) * 100,
    0
)

df["Engagement Rate"] = (
    df["Engagement Rate"]
    .fillna(pd.Series(calculated_engagement, index=df.index))
)

df["Engagement Rate"] = df["Engagement Rate"].clip(lower=0)


# Additional calculated metrics

df["Like Rate"] = np.where(
    df["Views"] > 0,
    df["Likes"] / df["Views"] * 100,
    0
)

df["Comment Rate"] = np.where(
    df["Views"] > 0,
    df["Comments"] / df["Views"] * 100,
    0
)


# =====================================================
# DATE PROCESSING
# =====================================================

if COLUMN_MAP["published"]:

    df["Published Date"] = pd.to_datetime(
        df[COLUMN_MAP["published"]],
        errors="coerce",
        utc=True
    )

    df["Publish Month"] = (
        df["Published Date"].dt.month_name()
    )

    df["Publish Day"] = (
        df["Published Date"].dt.day_name()
    )

    df["Publish Hour"] = (
        df["Published Date"].dt.hour
    )


# =====================================================
# SIDEBAR NAVIGATION
# =====================================================

st.sidebar.markdown("# ▶️ YouTube Analytics")

st.sidebar.caption(
    "Interactive Business Intelligence Dashboard"
)

st.sidebar.markdown("---")

page = st.sidebar.radio(

    "NAVIGATION",

    [
        "🏠 Home",
        "📊 Overview",
        "🎬 Category Analysis",
        "📈 Channel Analysis",
        "⚡ Content Analysis",
        "❤️ Engagement Analysis",
        "💡 Business Insights",
        "📁 Data Explorer"
    ]

)


# =====================================================
# GLOBAL FILTERS
# =====================================================

st.sidebar.markdown("---")

st.sidebar.subheader("🔎 Dashboard Filters")

categories = sorted(
    df["Category"].unique().tolist()
)

channels = sorted(
    df["Channel"].unique().tolist()
)

upload_types = sorted(
    df["Upload Type"].unique().tolist()
)


selected_categories = st.sidebar.multiselect(
    "Select Categories",
    categories,
    default=categories
)


selected_channels = st.sidebar.multiselect(
    "Select Channels",
    channels,
    default=channels
)


selected_types = st.sidebar.multiselect(
    "Select Upload Types",
    upload_types,
    default=upload_types
)


filtered_df = df[

    df["Category"].isin(selected_categories)

    & df["Channel"].isin(selected_channels)

    & df["Upload Type"].isin(selected_types)

].copy()


st.sidebar.markdown("---")

st.sidebar.caption(
    f"Total Records: {len(df):,}"
)

st.sidebar.caption(
    "Developed using Python and Streamlit"
)


# =====================================================
# COMMON FUNCTIONS
# =====================================================

def format_number(value):

    if value >= 1_000_000_000:

        return f"{value / 1_000_000_000:.2f}B"

    elif value >= 1_000_000:

        return f"{value / 1_000_000:.2f}M"

    elif value >= 1000:

        return f"{value / 1000:.2f}K"

    return f"{value:,.0f}"


def chart_layout(fig, height=400):

    fig.update_layout(

        template=CHART_TEMPLATE,

        height=height,

        paper_bgcolor="#11182B",

        plot_bgcolor="#11182B",

        font=dict(
            color="white",
            size=12
        ),

        margin=dict(
            l=20,
            r=20,
            t=50,
            b=30
        ),

        legend=dict(
            bgcolor="rgba(0,0,0,0)"
        )

    )

    return fig


def show_kpis(data):

    if data.empty:

        st.warning("No records available for these filters.")

        return

    total_views = data["Views"].sum()

    total_likes = data["Likes"].sum()

    total_comments = data["Comments"].sum()

    avg_engagement = data["Engagement Rate"].mean()

    total_channels = data["Channel"].nunique()

    total_uploads = len(data)

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Total Views",
        format_number(total_views)
    )

    c2.metric(
        "Total Likes",
        format_number(total_likes)
    )

    c3.metric(
        "Total Comments",
        format_number(total_comments)
    )

    c4, c5, c6 = st.columns(3)

    c4.metric(
        "Average Engagement",
        f"{avg_engagement:.2f}%"
    )

    c5.metric(
        "Total Channels",
        f"{total_channels:,}"
    )

    c6.metric(
        "Total Uploads",
        f"{total_uploads:,}"
    )


def show_description(text):

    st.markdown(
        f"""
        <div style="
        background:#17233D;
        padding:15px;
        border-radius:10px;
        border-left:4px solid #7667F5;
        margin-bottom:15px;
        ">
        {text}
        </div>
        """,
        unsafe_allow_html=True
    )


def show_chart(fig):

    st.plotly_chart(
        chart_layout(fig),
        use_container_width=True,
        config={"displayModeBar": True}
    )


# =====================================================
# HOME PAGE
# =====================================================

if page == "🏠 Home":

    st.title("▶️ YouTube Analytics Platform")

    st.markdown(
        "### Turning YouTube Data into Business Insights"
    )

    st.markdown("---")

    st.markdown(
        """
        Welcome to our YouTube Analytics Dashboard.

        This platform analyzes YouTube content performance,
        channel popularity, video categories and audience
        engagement to identify meaningful business insights.
        """
    )

    st.markdown("## 📊 Project Overview")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Total Videos",
        f"{len(df):,}"
    )

    c2.metric(
        "YouTube Channels",
        f"{df['Channel'].nunique():,}"
    )

    c3.metric(
        "Categories",
        f"{df['Category'].nunique():,}"
    )

    st.markdown("---")

    st.subheader("🎯 Project Objectives")

    st.write("""
    - Analyze category-wise YouTube performance.
    - Identify popular YouTube channels.
    - Compare Shorts and regular videos.
    - Understand audience engagement.
    - Discover content performance opportunities.
    - Generate actionable business recommendations.
    """)

    st.markdown("---")

    st.subheader("📌 Our Analysis Areas")

    col1, col2 = st.columns(2)

    with col1:

        st.info("🎬 Category Performance Analysis")

        st.info("📈 Channel Competition Analysis")

        st.info("⚡ Shorts vs Regular Videos")

    with col2:

        st.info("❤️ Audience Engagement Analysis")

        st.info("💡 Business Recommendations")

        st.info("📊 Interactive Data Exploration")


# =====================================================
# OVERVIEW PAGE
# =====================================================

elif page == "📊 Overview":

    st.title("📊 Executive Overview")

    st.caption(
        "A complete snapshot of YouTube performance."
    )

    show_kpis(filtered_df)

    st.markdown("---")

    if filtered_df.empty:

        st.warning("No data available.")

    else:

        col1, col2 = st.columns(2)

        # Category views

        with col1:

            st.subheader("Views by Category")

            category_views = (
                filtered_df.groupby("Category")["Views"]
                .sum()
                .reset_index()
                .sort_values("Views", ascending=False)
            )

            fig = px.bar(
                category_views,
                x="Category",
                y="Views",
                color="Category",
                color_discrete_sequence=COLORS,
                title="Total Views by Category"
            )

            show_chart(fig)

        # Upload distribution

        with col2:

            st.subheader("Upload Distribution")

            type_counts = (
                filtered_df["Upload Type"]
                .value_counts()
                .reset_index()
            )

            type_counts.columns = [
                "Upload Type",
                "Count"
            ]

            fig = px.pie(
                type_counts,
                names="Upload Type",
                values="Count",
                hole=0.55,
                color_discrete_sequence=COLORS,
                title="Content Type Distribution"
            )

            show_chart(fig)

        # Top channels

        st.subheader("Top 10 Channels")

        top_channels = (
            filtered_df.groupby("Channel")["Views"]
            .sum()
            .nlargest(10)
            .reset_index()
        )

        fig = px.bar(
            top_channels,
            x="Views",
            y="Channel",
            orientation="h",
            color="Views",
            color_continuous_scale="Purples"
        )

        fig.update_yaxes(
            categoryorder="total ascending"
        )

        show_chart(fig)


# =====================================================
# CATEGORY ANALYSIS
# =====================================================

elif page == "🎬 Category Analysis":

    st.title("🎬 Category Performance Analysis")

    show_description(
        "Understand which YouTube categories attract "
        "the highest views and audience engagement."
    )

    if not filtered_df.empty:

        category_summary = (
            filtered_df.groupby("Category")
            .agg(
                Total_Views=("Views", "sum"),
                Average_Views=("Views", "mean"),
                Total_Likes=("Likes", "sum"),
                Total_Comments=("Comments", "sum"),
                Average_Engagement=("Engagement Rate", "mean"),
                Uploads=("Views", "count")
            )
            .reset_index()
        )

        category_summary = category_summary.sort_values(
            "Total_Views",
            ascending=False
        )

        col1, col2 = st.columns(2)

        with col1:

            fig = px.bar(
                category_summary,
                x="Category",
                y="Total_Views",
                color="Total_Views",
                color_continuous_scale="Purples",
                title="Total Views by Category"
            )

            show_chart(fig)

        with col2:

            fig = px.bar(
                category_summary.sort_values(
                    "Average_Views",
                    ascending=False
                ),
                x="Category",
                y="Average_Views",
                color="Average_Views",
                color_continuous_scale="Teal",
                title="Average Views by Category"
            )

            show_chart(fig)

        col3, col4 = st.columns(2)

        with col3:

            fig = px.bar(
                category_summary,
                x="Category",
                y="Total_Likes",
                title="Likes by Category",
                color="Category",
                color_discrete_sequence=COLORS
            )

            show_chart(fig)

        with col4:

            fig = px.bar(
                category_summary,
                x="Category",
                y="Average_Engagement",
                color="Category",
                color_discrete_sequence=COLORS,
                title="Average Engagement by Category"
            )

            show_chart(fig)

        st.subheader("Category Performance Table")

        st.dataframe(
            category_summary,
            use_container_width=True
        )


# =====================================================
# CHANNEL ANALYSIS
# =====================================================

elif page == "📈 Channel Analysis":

    st.title("📈 YouTube Channel Analysis")

    show_description(
        "Identify leading YouTube channels and compare "
        "their popularity, views and engagement."
    )

    if not filtered_df.empty:

        channel_summary = (
            filtered_df.groupby("Channel")
            .agg(
                Total_Views=("Views", "sum"),
                Average_Views=("Views", "mean"),
                Total_Likes=("Likes", "sum"),
                Total_Comments=("Comments", "sum"),
                Average_Engagement=("Engagement Rate", "mean"),
                Uploads=("Views", "count")
            )
            .reset_index()
        )

        top10 = channel_summary.nlargest(
            10,
            "Total_Views"
        )

        col1, col2 = st.columns(2)

        with col1:

            fig = px.bar(
                top10.sort_values("Total_Views"),
                x="Total_Views",
                y="Channel",
                orientation="h",
                color="Total_Views",
                color_continuous_scale="Purples",
                title="Top 10 Channels by Views"
            )

            show_chart(fig)

        with col2:

            top_engagement = channel_summary.nlargest(
                10,
                "Average_Engagement"
            )

            fig = px.bar(
                top_engagement,
                x="Channel",
                y="Average_Engagement",
                color="Average_Engagement",
                color_continuous_scale="Teal",
                title="Top 10 Engagement Channels"
            )

            show_chart(fig)

        st.subheader("Channel Performance Comparison")

        selected = st.multiselect(
            "Compare Channels",
            channel_summary["Channel"].tolist(),
            default=top10["Channel"].head(5).tolist()
        )

        comparison = channel_summary[
            channel_summary["Channel"].isin(selected)
        ]

        fig = px.scatter(
            comparison,
            x="Total_Views",
            y="Average_Engagement",
            size="Uploads",
            color="Channel",
            hover_data=[
                "Total_Likes",
                "Total_Comments"
            ],
            title="Channel Views vs Engagement"
        )

        show_chart(fig)

        st.dataframe(
            channel_summary.sort_values(
                "Total_Views",
                ascending=False
            ),
            use_container_width=True
        )


# =====================================================
# CONTENT ANALYSIS
# =====================================================

elif page == "⚡ Content Analysis":

    st.title("⚡ Content Performance Analysis")

    show_description(
        "Compare Shorts and regular videos to understand "
        "which content format performs better."
    )

    if not filtered_df.empty:

        content_summary = (
            filtered_df.groupby("Upload Type")
            .agg(
                Total_Views=("Views", "sum"),
                Average_Views=("Views", "mean"),
                Total_Likes=("Likes", "sum"),
                Total_Comments=("Comments", "sum"),
                Uploads=("Views", "count"),
                Engagement=("Engagement Rate", "mean")
            )
            .reset_index()
        )

        col1, col2 = st.columns(2)

        with col1:

            fig = px.bar(
                content_summary,
                x="Upload Type",
                y="Average_Views",
                color="Upload Type",
                color_discrete_sequence=COLORS,
                title="Average Views: Shorts vs Videos"
            )

            show_chart(fig)

        with col2:

            fig = px.pie(
                content_summary,
                names="Upload Type",
                values="Uploads",
                hole=0.5,
                title="Content Upload Distribution",
                color_discrete_sequence=COLORS
            )

            show_chart(fig)

        col3, col4 = st.columns(2)

        with col3:

            fig = px.bar(
                content_summary,
                x="Upload Type",
                y="Total_Views",
                color="Upload Type",
                color_discrete_sequence=COLORS,
                title="Total Views by Content Type"
            )

            show_chart(fig)

        with col4:

            fig = px.bar(
                content_summary,
                x="Upload Type",
                y="Engagement",
                color="Upload Type",
                color_discrete_sequence=COLORS,
                title="Engagement by Content Type"
            )

            show_chart(fig)

        st.subheader("Content Performance Summary")

        st.dataframe(
            content_summary,
            use_container_width=True
        )


# =====================================================
# ENGAGEMENT ANALYSIS
# =====================================================

elif page == "❤️ Engagement Analysis":

    st.title("❤️ Audience Engagement Analysis")

    show_description(
        "Explore how views, likes and comments relate "
        "to audience engagement."
    )

    if not filtered_df.empty:

        col1, col2 = st.columns(2)

        with col1:

            fig = px.scatter(
                filtered_df,
                x="Views",
                y="Likes",
                color="Upload Type",
                size="Comments",
                hover_data=["Channel", "Category"],
                title="Views vs Likes"
            )

            show_chart(fig)

        with col2:

            fig = px.scatter(
                filtered_df,
                x="Views",
                y="Engagement Rate",
                color="Category",
                hover_data=["Channel"],
                title="Views vs Engagement Rate"
            )

            show_chart(fig)

        # Engagement segmentation

        st.subheader("Audience Engagement Segmentation")

        median_views = filtered_df["Views"].median()

        median_engagement = (
            filtered_df["Engagement Rate"].median()
        )

        def classify(row):

            high_views = row["Views"] >= median_views

            high_engagement = (
                row["Engagement Rate"] >= median_engagement
            )

            if high_views and high_engagement:

                return "High Views + High Engagement"

            elif high_views:

                return "High Views + Low Engagement"

            elif high_engagement:

                return "Low Views + High Engagement"

            return "Low Views + Low Engagement"


        filtered_df["Audience Segment"] = (
            filtered_df.apply(classify, axis=1)
        )

        segments = (
            filtered_df["Audience Segment"]
            .value_counts()
            .reset_index()
        )

        segments.columns = [
            "Segment",
            "Videos"
        ]

        fig = px.pie(
            segments,
            names="Segment",
            values="Videos",
            hole=0.45,
            color_discrete_sequence=COLORS,
            title="Audience Engagement Segments"
        )

        show_chart(fig)

        st.dataframe(
            segments,
            use_container_width=True
        )

        st.info("""
        Business interpretation:

        1. High Views + High Engagement:
           Strong-performing content.

        2. High Views + Low Engagement:
           Opportunity to improve audience interaction.

        3. Low Views + High Engagement:
           Content has an engaged audience but needs more reach.

        4. Low Views + Low Engagement:
           Content may need improvements in reach and quality.
        """)


# =====================================================
# BUSINESS INSIGHTS
# =====================================================

elif page == "💡 Business Insights":

    st.title("💡 Business Insights & Recommendations")

    st.markdown(
        "Transforming analytical findings into practical "
        "content strategy recommendations."
    )

    if not filtered_df.empty:

        category_summary = (
            filtered_df.groupby("Category")
            .agg(
                Total_Views=("Views", "sum"),
                Average_Views=("Views", "mean"),
                Engagement=("Engagement Rate", "mean")
            )
        )

        best_total = category_summary[
            "Total_Views"
        ].idxmax()

        best_average = category_summary[
            "Average_Views"
        ].idxmax()

        best_engagement = category_summary[
            "Engagement"
        ].idxmax()

        channel_summary = (
            filtered_df.groupby("Channel")["Views"]
            .sum()
        )

        top_channel = channel_summary.idxmax()

        st.markdown("---")

        st.subheader("📊 Key Discoveries")

        st.success(
            f"🏆 Highest total views category: {best_total}"
        )

        st.success(
            f"🚀 Highest average views category: {best_average}"
        )

        st.success(
            f"❤️ Highest engagement category: {best_engagement}"
        )

        st.success(
            f"📈 Leading channel by views: {top_channel}"
        )

        st.markdown("---")

        st.subheader("🎯 Business Recommendations")

        st.markdown("""
        **1. Category Strategy**

        Focus on categories that generate high total views.
        Explore categories with high average views to identify
        additional content opportunities.

        **2. Content Format Strategy**

        Compare Shorts and regular videos to understand
        which format attracts more views and engagement.

        **3. Channel Growth Strategy**

        Study successful channels to understand their
        content performance and identify competitive opportunities.

        **4. Audience Engagement Strategy**

        Encourage likes, comments and audience participation.
        Improve interaction for videos with high views
        but low engagement.

        **5. Content Improvement Strategy**

        Identify low-performing videos and study their
        category, upload type and engagement patterns.
        """)

        st.markdown("---")

        st.subheader("📌 Four Audience Segments")

        st.write("""
        - High Views + High Engagement: Maintain the strategy.
        - High Views + Low Engagement: Improve interaction.
        - Low Views + High Engagement: Increase reach.
        - Low Views + Low Engagement: Improve content strategy.
        """)

        st.caption(
            "Note: Recommendations are based on observed "
            "dataset patterns, not proof of causation."
        )


# =====================================================
# DATA EXPLORER
# =====================================================

elif page == "📁 Data Explorer":

    st.title("📁 YouTube Data Explorer")

    st.markdown(
        "Explore, search and download the analyzed dataset."
    )

    search = st.text_input(
        "🔎 Search channel or category"
    )

    display_df = filtered_df.copy()

    if search:

        mask = (
            display_df["Channel"].str.contains(
                search,
                case=False,
                na=False
            )
            |
            display_df["Category"].str.contains(
                search,
                case=False,
                na=False
            )
        )

        display_df = display_df[mask]

    st.markdown("---")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Filtered Records",
        f"{len(display_df):,}"
    )

    c2.metric(
        "Channels",
        f"{display_df['Channel'].nunique():,}"
    )

    c3.metric(
        "Total Views",
        format_number(display_df["Views"].sum())
    )

    st.subheader("Dataset Preview")

    st.dataframe(
        display_df,
        use_container_width=True,
        height=450
    )

    st.markdown("---")

    st.subheader("⬇️ Download Analysis Results")

    csv = display_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Filtered Dataset CSV",
        data=csv,
        file_name="youtube_analysis_results.csv",
        mime="text/csv"
    )


# =====================================================
# FOOTER
# =====================================================

st.markdown("---")

st.markdown(
    """
    <div style="text-align:center; color:#8998B5;">

    <h4>YouTube Analytics Dashboard</h4>

    Built with Python | Pandas | Plotly | Streamlit

    Data-Driven Insights for YouTube Content Performance

    </div>
    """,
    unsafe_allow_html=True
)