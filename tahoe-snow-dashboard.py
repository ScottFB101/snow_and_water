import streamlit as st
import requests
import polars as pl
import altair as alt
from datetime import timedelta

# Page configuration
st.set_page_config(
    page_title="Palisades Tahoe Snow Conditions",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Ideas:
#   1. Dataframe with Linechart for snow history, or some chart
#   2. For Temp chart, do layerchart here 'https://github.com/jakevdp/altair-examples/blob/master/notebooks/MLB_Strikeouts.ipynb"
#   3. Heatmap to visualize Year, Month, and some value (Snow Depth, Temp, etc)


# Inject Tailwind CSS and modern styling
st.markdown(
    """
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
    :root {
        --primary-blue: #0369A1;
        --primary-blue-light: #0EA5E9;
        --slate-900: #0C4A6E;
        --slate-800: #164E63;
        --slate-700: #164E63;
        --slate-300: #E0F2FE;
        --slate-100: #F0F9FF;
        --slate-50: #F0F9FF;
        --cyan-50: #F0F9FF;
        --cyan-500: #10B981;
        --amber-500: #F59E0B;
        --purple-600: #7C3AED;
        --slate-400: #38BDF8;
    }
    
    * {
        --tw-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    body, html {
        background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Helvetica Neue", sans-serif;
    }
    
    /* Override Streamlit's default dark theme */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%) !important;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #E0F2FE 0%, #BAE6FD 100%) !important;
    }
    
    .main {
        padding: 2rem 1rem;
        background: transparent !important;
    }
    
    section[data-testid="stAppViewContainer"] > div:first-child {
        background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%) !important;
    }
    
    /* Modern Metric Cards with Tailwind */
    .metric-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F0F9FF 100%);
        border: 2px solid #E0F2FE;
        border-radius: 1.25rem;
        padding: 2rem;
        box-shadow: 0 10px 30px -5px rgba(3, 105, 161, 0.08);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(10px);
    }
    
    .metric-card:hover {
        transform: translateY(-6px) translateX(0);
        box-shadow: 0 20px 40px -10px rgba(3, 105, 161, 0.2);
        border-color: #BAE6FD;
        background: linear-gradient(135deg, #FFFFFF 0%, #E0F2FE 100%);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, #0369A1 0%, #0EA5E9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #0C4A6E;
        margin-top: 0.75rem;
        font-weight: 500;
        letter-spacing: 0.025em;
        text-transform: capitalize;
    }
    
    /* Header Styling */
    h1 {
        background: linear-gradient(135deg, #0369A1 0%, #0EA5E9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
        font-size: 2.5rem;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem;
    }
    
    h2 {
        color: #0369A1;
        font-weight: 700;
        font-size: 1.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    /* Subheader */
    .subheader-text {
        color: #0C4A6E;
        font-size: 1rem;
        font-weight: 500;
        letter-spacing: 0.01em;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] button {
        border-radius: 0.75rem;
        border: 1px solid transparent;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        color: #0C4A6E;
        transition: all 0.3s ease;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab-list"] button:hover {
        color: #0369A1;
        background-color: rgba(3, 105, 161, 0.05);
        border-color: rgba(3, 105, 161, 0.15);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(3, 105, 161, 0.1) 0%, rgba(14, 165, 233, 0.08) 100%);
        color: #0369A1 !important;
        border-color: #0369A1 !important;
    }
    
    /* Chart Container Styling */
    .stVegaLiteChart {
        border-radius: 1.25rem;
        overflow: hidden;
        box-shadow: 0 10px 25px -5px rgba(3, 105, 161, 0.1);
        transition: all 0.3s ease;
    }
    
    .stVegaLiteChart:hover {
        box-shadow: 0 15px 35px -5px rgba(3, 105, 161, 0.18);
    }
    
    /* Divider Styling */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #BAE6FD, transparent);
        margin: 2rem 0;
    }
    
    /* Caption and Text */
    .caption-text {
        color: #0C4A6E;
        font-size: 0.85rem;
        font-weight: 500;
        letter-spacing: 0.01em;
    }
    
    /* Markdown Content Styling */
    .stMarkdown h3 {
        color: #0369A1;
        font-weight: 700;
        font-size: 1.25rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .stMarkdown p {
        color: #0C4A6E;
        line-height: 1.6;
        font-size: 0.95rem;
    }
    
    /* Table Styling */
    .stMarkdown table {
        border-collapse: collapse;
        width: 100%;
        margin: 1rem 0;
        border-radius: 0.75rem;
        overflow: hidden;
        box-shadow: 0 4px 12px -2px rgba(3, 105, 161, 0.1);
    }
    
    .stMarkdown table th {
        background: linear-gradient(135deg, #E0F2FE 0%, #BAE6FD 100%);
        color: #0369A1;
        font-weight: 700;
        padding: 1rem;
        text-align: left;
        border-bottom: 2px solid #38BDF8;
    }
    
    .stMarkdown table td {
        color: #0C4A6E;
        padding: 0.875rem 1rem;
        border-bottom: 1px solid #E0F2FE;
    }
    
    .stMarkdown table tbody tr:hover {
        background-color: #F0F9FF;
    }
    
    /* Spinner */
    .stSpinner {
        text-align: center;
    }
    
    /* Success and Error Messages */
    .stSuccess, .stError, .stInfo {
        border-radius: 1rem;
        border: 1px solid;
        padding: 1.25rem 1.5rem;
        font-weight: 500;
    }
    
    .stSuccess {
        background-color: #ecfdf5;
        border-color: #a7f3d0;
        color: #065f46;
    }
    
    .stError {
        background-color: #fef2f2;
        border-color: #fecaca;
        color: #7f1d1d;
    }
    
    .stInfo {
        background-color: #eff6ff;
        border-color: #bfdbfe;
        color: #1e40af;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main {
            padding: 1.5rem 1rem;
        }
        
        h1 {
            font-size: 2rem;
        }
        
        .metric-card {
            padding: 1.5rem;
        }
        
        .metric-value {
            font-size: 2rem;
        }
    }
    
    @media (max-width: 640px) {
        .main {
            padding: 1rem 0.75rem;
        }
        
        h1 {
            font-size: 1.75rem;
        }
        
        .metric-card {
            padding: 1.25rem;
        }
        
        .metric-value {
            font-size: 1.75rem;
        }
        
        .stTabs [data-baseweb="tab-list"] button {
            padding: 0.6rem 1rem;
            font-size: 0.85rem;
        }
    }
    </style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_weather_data():
    """Fetch weather data from USDA AWDB API with error handling"""
    duration = "HOURLY"
    elements = "SNWD%2CSNDN%2CSNRR%2CSWE%2CWTEQ%2CTOBS"
    start_date = "2025-10-01"

    url = f"https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data?stationTriplets=784%3ACA%3ASNTL&elements={elements}&duration={duration}&beginDate={start_date}&periodRef=END&centralTendencyType=NONE&returnFlags=false&returnOriginalValues=false&returnSuspectData=false"

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()

        # Validate response structure
        if not isinstance(data, list) or len(data) == 0:
            raise ValueError("Invalid API response structure")
        if "data" not in data[0]:
            raise ValueError("Missing 'data' field in API response")

        return data
    except requests.exceptions.Timeout:
        raise Exception("API request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise Exception("Connection error. Please check your internet connection.")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"API error: {e.response.status_code}")
    except ValueError as e:
        raise Exception(f"Invalid API response: {str(e)}")


@st.cache_data(ttl=3600)
def process_weather_data(weather_data_json):
    """Process raw weather data into a structured dataframe"""
    weather_data_list = []

    for station in weather_data_json:
        station_triplet = station["stationTriplet"]
        for measurement in station["data"]:
            element_code = measurement["stationElement"]["elementCode"]
            for val in measurement["values"]:
                weather_data_list.append(
                    {
                        "stationTriplet": station_triplet,
                        "elementCode": element_code,
                        "date": val["date"],
                        "value": val["value"],
                    }
                )

    weather_data_df = pl.DataFrame(weather_data_list)
    weather_data_df = weather_data_df.with_columns(
        [
            pl.col("stationTriplet").cast(pl.Categorical),
            pl.col("elementCode").cast(pl.Categorical),
            pl.col("date").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M"),
        ]
    )

    # Pivot to get elements as columns
    weather_data_df = weather_data_df.pivot(values="value", columns="elementCode")

    # Sort by date to ensure forward-fill works correctly
    weather_data_df = weather_data_df.sort("date")

    # Forward-fill WTEQ (daily measurement) to fill hourly gaps
    weather_data_df = weather_data_df.with_columns(pl.col("WTEQ").forward_fill())

    # Add snow_density column using correct formula: ρ_s = (ρ_w * SWE) / D
    # Both WTEQ and SNWD are in inches, so result is in kg/m³
    # Only compute density where both values are positive and valid
    weather_data_df = weather_data_df.with_columns(
        pl.when(
            (pl.col("WTEQ").is_not_null())
            & (pl.col("SNWD").is_not_null())
            & (pl.col("SNWD") > 0)
        )
        .then(1000.0 * pl.col("WTEQ") / pl.col("SNWD"))
        .otherwise(None)
        .alias("snow_density")
    )

    return weather_data_df


# Chart styling helpers
CHART_CONFIG = {
    "bg": "#F9FBFD",
    "title_color": "#2E3440",
    "axis_label_color": "#A8B3C7",
    "grid_color": "#EEF2F7",
    "font_size": 11,
    "title_font_size": 12,
}


def create_axis(grid=True):
    """Create standardized axis configuration"""
    return alt.Axis(
        grid=grid,
        gridColor=CHART_CONFIG["grid_color"] if grid else None,
        domain=False,
        tickSize=0,
        labelColor=CHART_CONFIG["axis_label_color"],
    )


def configure_chart(chart, title, height=400, legend=False):
    """Apply consistent styling to charts"""
    config = (
        chart.properties(
            background=CHART_CONFIG["bg"],
            height=height,
            title=alt.TitleParams(
                text=title,
                anchor="start",
                fontSize=16,
                color=CHART_CONFIG["title_color"],
            ),
        )
        .configure_view(stroke=None)
        .configure_axis(
            labelFontSize=CHART_CONFIG["font_size"],
            titleFontSize=CHART_CONFIG["title_font_size"],
        )
    )
    if legend:
        config = config.configure_legend(
            labelFontSize=CHART_CONFIG["font_size"],
            titleFontSize=CHART_CONFIG["title_font_size"],
        )
    return config


def render_metric_card(value, unit, label, change_percent=None, change_direction=None):
    """Helper to render metric cards with consistent styling and percent change"""
    display_value = f"{value}{unit}" if value is not None else "N/A"

    # Build change indicator HTML
    change_html = ""
    if change_percent is not None and change_direction is not None:
        # If change is 0, show gray text with no arrow
        if change_percent == 0:
            change_html = '<p style="font-size: 0.75rem; color: #9CA3AF; margin-top: 0.5rem; font-weight: 600;">0.0% vs yesterday</p>'
        else:
            arrow = "↑" if change_direction == "up" else "↓"
            color = (
                "#10B981" if change_direction == "up" else "#EF4444"
            )  # Green up, Red down
            change_html = f'<p style="font-size: 0.75rem; color: {color}; margin-top: 0.5rem; font-weight: 600;">{arrow} {abs(change_percent):.1f}% vs yesterday</p>'

    return f"""
                <div class="metric-card">
                    <p class="metric-value">{display_value}</p>
                    <p class="metric-label">{label}</p>
                    {change_html}
                </div>
            """


def get_latest_metrics(df):
    """Get the latest values for each metric with fallback for missing data"""
    if df.is_empty():
        raise ValueError("No data available")

    metrics = {}
    latest_date = df.select(pl.col("date").max()).item()

    # Get latest values for each element
    latest_row = df.filter(pl.col("date") == latest_date).row(0, named=True)

    for element in ["SNWD", "TOBS", "WTEQ"]:
        value = latest_row.get(element)
        if value is not None:
            metrics[element] = value
        else:
            # Fallback to most recent available value
            available = df.select(element).drop_nulls()
            if available.height > 0:
                metrics[element] = available.item(-1, 0)
            else:
                metrics[element] = None

    return metrics, latest_date


def get_day_over_day_changes(df):
    """Calculate percent change between today and yesterday using average values for key metrics"""
    if df.is_empty():
        return {}

    # Get today's date (most recent)
    latest_date = df.select(pl.col("date").max()).item()
    today = latest_date.date()
    yesterday = today - timedelta(days=1)

    # Filter data for each day and compute daily averages
    today_data = df.filter(pl.col("date").cast(pl.Date) == today).select(
        pl.col("SNWD").mean().alias("snwd"),
        pl.col("TOBS").mean().alias("tobs"),
        pl.col("WTEQ").mean().alias("wteq"),
    )

    yesterday_data = df.filter(pl.col("date").cast(pl.Date) == yesterday).select(
        pl.col("SNWD").mean().alias("snwd"),
        pl.col("TOBS").mean().alias("tobs"),
        pl.col("WTEQ").mean().alias("wteq"),
    )

    changes = {}

    # Only calculate changes if both days have data
    if today_data.height > 0 and yesterday_data.height > 0:
        today_row = today_data.row(0, named=True)
        yesterday_row = yesterday_data.row(0, named=True)

        # Snow Depth change
        if (
            yesterday_row.get("snwd")
            and today_row.get("snwd")
            and yesterday_row["snwd"] != 0
        ):
            snwd_change = (
                (today_row["snwd"] - yesterday_row["snwd"]) / yesterday_row["snwd"]
            ) * 100
            changes["snwd_percent"] = snwd_change
            changes["snwd_direction"] = "up" if snwd_change >= 0 else "down"

        # Temperature change
        if (
            yesterday_row.get("tobs")
            and today_row.get("tobs")
            and yesterday_row["tobs"] != 0
        ):
            tobs_change = (
                (today_row["tobs"] - yesterday_row["tobs"]) / abs(yesterday_row["tobs"])
            ) * 100
            changes["tobs_percent"] = tobs_change
            changes["tobs_direction"] = "up" if tobs_change >= 0 else "down"

        # SWE change
        if (
            yesterday_row.get("wteq")
            and today_row.get("wteq")
            and yesterday_row["wteq"] != 0
        ):
            wteq_change = (
                (today_row["wteq"] - yesterday_row["wteq"]) / yesterday_row["wteq"]
            ) * 100
            changes["wteq_percent"] = wteq_change
            changes["wteq_direction"] = "up" if wteq_change >= 0 else "down"

    return changes


# Main app
st.title("Palisades Tahoe Snow Conditions")
st.markdown(
    '<p class="subheader-text">❄️ Real-time snow and weather data from USDA SNOTEL Station</p>',
    unsafe_allow_html=True,
)

# Fetch and process data
with st.spinner("Loading latest conditions..."):
    try:
        weather_data_json = fetch_weather_data()
        weather_df = process_weather_data(weather_data_json)
        metrics, latest_date = get_latest_metrics(weather_df)

        # Display last update time
        st.markdown(
            f'<p class="caption-text">🕐 Last updated: {latest_date.strftime("%B %d, %Y at %I:%M %p")}</p>',
            unsafe_allow_html=True,
        )

        # Get day-over-day changes (average values)
        day_changes = get_day_over_day_changes(weather_df)

        # Current conditions metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                render_metric_card(
                    metrics.get("SNWD"),
                    '"',
                    "Snow Depth",
                    change_percent=day_changes.get("snwd_percent"),
                    change_direction=day_changes.get("snwd_direction"),
                ),
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                render_metric_card(
                    metrics.get("TOBS"),
                    "°F",
                    "Temperature",
                    change_percent=day_changes.get("tobs_percent"),
                    change_direction=day_changes.get("tobs_direction"),
                ),
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                render_metric_card(
                    metrics.get("WTEQ"),
                    '"',
                    "Snow Water Equivalent",
                    change_percent=day_changes.get("wteq_percent"),
                    change_direction=day_changes.get("wteq_direction"),
                ),
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts section
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Snow Depth", "Temperature", "Snow Water Equivalent", "Snow Density"]
        )

        with tab1:
            # Base chart with x-axis encoding
            base = alt.Chart(weather_df).encode(
                x=alt.X("date:T", title="", axis=create_axis(grid=False))
            )

            # Snow depth area chart
            snow_area = base.mark_area(
                color="lightblue", interpolate="step-after", line=True
            ).encode(y=alt.Y("SNWD:Q", title="Snow Depth (Inches)", axis=create_axis()))

            snow_depth_chart = configure_chart(snow_area, "Snow Depth Over Time")
            st.altair_chart(snow_depth_chart)

        with tab2:
            # Temperature Chart
            temp_line = (
                alt.Chart(weather_df)
                .mark_line(color="#f59e0b", size=2, point=False)
                .encode(
                    x=alt.X("date:T", title="", axis=create_axis(grid=False)),
                    y=alt.Y("TOBS:Q", title="Temperature (°F)", axis=create_axis()),
                    tooltip=["date:T", alt.Tooltip("TOBS:Q", format=".1f")],
                    color=alt.value("#f59e0b"),
                )
            )

            # Freezing point reference line
            freezing_line = (
                alt.Chart(pl.DataFrame({"freezing_point": [32]}))
                .mark_rule(strokeDash=[5, 5], color="lightblue", size=2)
                .encode(y="freezing_point:Q", color=alt.value("lightblue"))
            )

            # Legend layer
            legend_data = pl.DataFrame(
                {
                    "legend": ["Observed Temperature", "Freezing Point (32°F)"],
                    "value": [0, 0],
                }
            )
            legend_layer = (
                alt.Chart(legend_data)
                .mark_point(opacity=0)
                .encode(
                    color=alt.Color(
                        "legend:N",
                        scale=alt.Scale(
                            domain=["Observed Temperature", "Freezing Point (32°F)"],
                            range=["#f59e0b", "lightblue"],
                        ),
                        legend=alt.Legend(
                            title="Legend", titleFontSize=12, labelFontSize=11
                        ),
                    )
                )
            )

            temp_chart = configure_chart(
                temp_line + freezing_line + legend_layer,
                "Temperature Over Time",
                legend=True,
            )
            st.altair_chart(temp_chart, use_container_width=True)

        with tab3:
            # SWE Chart
            swe_area = (
                alt.Chart(weather_df)
                .mark_area(
                    color="#06b6d4", opacity=0.3, interpolate="step-after", line=True
                )
                .encode(
                    x=alt.X("date:T", title="", axis=create_axis(grid=False)),
                    y=alt.Y("WTEQ:Q", title="SWE (inches)", axis=create_axis()),
                    tooltip=["date:T", alt.Tooltip("WTEQ:Q", format=".2f")],
                )
            )

            swe_chart = configure_chart(swe_area, "Snow Water Equivalent Over Time")
            st.altair_chart(swe_chart, use_container_width=True)

            st.markdown("---")
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown(
                """💧 **Understanding Snow Water Equivalent (SWE)**

SWE measures the amount of water contained in the snowpack, expressed in inches. It represents how much liquid water you would have if all the snow melted. This is critical for water resource planning and helps predict runoff and water availability throughout the year.

🎿 **For Skiers**: Higher SWE indicates a denser, more stable snowpack with greater water content. This often means longer-lasting snow conditions and better base stability. Rising SWE suggests fresh snow has fallen.

📊 **SWE vs. Snow Depth**: Snow depth alone can be misleading—light, fluffy powder creates deep snow with low SWE, while heavy, wet snow creates less depth but higher SWE. Comparing both metrics shows the complete snowpack picture."""
            )

        with tab4:
            # Filter to rows with valid snow_density
            valid_density_df = weather_df.filter(pl.col("WTEQ") & pl.col("SNWD") > 0)
            mean_density = valid_density_df.select(pl.col("snow_density").mean()).item()

            # Base chart
            base = alt.Chart(valid_density_df).encode(
                x=alt.X("date:T", title="", axis=create_axis(grid=False))
            )

            # Snow density area
            density_area = base.mark_area(interpolate="basis", opacity=0.6).encode(
                y=alt.Y(
                    "snow_density:Q",
                    title="Snow Density (WTEQ / SNWD)",
                    axis=create_axis(),
                ),
                color=alt.value("#efe6ff"),
                tooltip=["date:T", alt.Tooltip("snow_density:Q", format=".3f")],
            )

            # 24-hour rolling mean
            rolling_mean = (
                base.transform_window(
                    rolling_mean="mean(snow_density)",
                    frame=[-23, 0],
                    sort=[{"field": "date", "order": "ascending"}],
                )
                .mark_line(color="#7c3aed", size=2)
                .encode(y=alt.Y("rolling_mean:Q"), color=alt.value("#7c3aed"))
            )

            # Overall mean reference line
            mean_rule = (
                alt.Chart(pl.DataFrame({"mean_density": [mean_density]}))
                .mark_rule(color="#94a3b8", strokeDash=[4, 4], size=2)
                .encode(y="mean_density:Q", color=alt.value("#94a3b8"))
            )

            # Legend layer
            legend_data = pl.DataFrame(
                {
                    "legend": ["Snow Density", "24-Hour Rolling Mean", "Overall Mean"],
                    "value": [0, 0, 0],
                }
            )
            legend_layer = (
                alt.Chart(legend_data)
                .mark_point(opacity=0)
                .encode(
                    color=alt.Color(
                        "legend:N",
                        scale=alt.Scale(
                            domain=[
                                "Snow Density",
                                "24-Hour Rolling Mean",
                                "Overall Mean",
                            ],
                            range=["#efe6ff", "#7c3aed", "#94a3b8"],
                        ),
                        legend=alt.Legend(
                            title="Legend", titleFontSize=12, labelFontSize=11
                        ),
                    )
                )
            )

            density_chart = configure_chart(
                density_area + rolling_mean + mean_rule + legend_layer,
                "Snow Density Over Time (WTEQ / SNWD)",
                height=420,
                legend=True,
            )
            st.altair_chart(density_chart, use_container_width=True)

            st.markdown("---")
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown(
                """❄️ **Understanding Snow Density (kg/m³)**

Snow density reveals the type and condition of snow. Calculated as ρ_s = (1000 × WTEQ) / SNWD in kg/m³. Lower density indicates lighter, fluffier snow, while higher density suggests heavier, more compacted or wet snow.

| Condition | Range | Description |
|-----------|-------|-------------|
| 🎿 Wild/Fresh Snow | 10 - 30 | Lightly compacted, freshly fallen powder. Ideal skiing conditions. |
| ⛷️ New & Settling | 50 - 90 | Recently fallen snow beginning to settle and compress. |
| 💨 Wind-Toughened | ~280 | Dense snow compacted by wind. Good stability, harder to ski. |
| 🧊 Hard Slab & Ice | ≥ 350 | Wind slab or refrozen ice. Hazardous and difficult terrain. |"""
            )

        # Statistics section
        st.markdown("### 📈 30-Day Statistics")
        col1, col2, col3, col4 = st.columns(4)

        # Compute all stats in single batch operation
        stats = weather_df.select(
            pl.col("SNWD").max().alias("max_snow"),
            pl.col("SNWD").mean().alias("avg_snow"),
            pl.col("TOBS").max().alias("max_temp"),
            pl.col("TOBS").min().alias("min_temp"),
        ).row(0, named=True)

        # Modern stat cards with Tailwind-inspired styling
        stat_items = [
            ("Max Snow Depth", f'{stats["max_snow"]:.0f}"', "❄️"),
            ("Avg Snow Depth", f'{stats["avg_snow"]:.1f}"', "📏"),
            ("Max Temperature", f"{stats['max_temp']:.0f}°F", "🔥"),
            ("Min Temperature", f"{stats['min_temp']:.0f}°F", "❄️"),
        ]

        cols = [col1, col2, col3, col4]
        for col, (label, value, emoji) in zip(cols, stat_items):
            with col:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <p class="metric-label">{emoji} {label}</p>
                        <p class="metric-value">{value}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info(
            "Please try refreshing the page. If the problem persists, the USDA API may be temporarily unavailable."
        )

# Footer
st.markdown("---")
st.markdown(
    '<p class="caption-text">🔗 Data source: USDA Natural Resources Conservation Service SNOTEL Network | Station: Palisades Tahoe (784:CA:SNTL)</p>',
    unsafe_allow_html=True,
)
