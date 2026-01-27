import streamlit as st
import requests
import polars as pl
import altair as alt

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


# Custom CSS for modern styling
st.markdown(
    """
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .metric-card {
    background: linear-gradient(145deg, #f5f5f7 0%, #ffffff 100%);
    padding: 2rem;
    border-radius: 18px;
    color: #1d1d1f;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(0, 0, 0, 0.04);
    transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }
    .metric-value {
        font-size: 3rem;
        font-weight: 600;
        margin: 0;
        background: linear-gradient(135deg, #0071e3 0%, #0077ed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
    }
    .metric-label {
        font-size: 0.95rem;
        color: #6e6e73;
        margin-top: 0.75rem;
        font-weight: 400;
        letter-spacing: 0.01em;
    }
    h1 {
        color: #1e293b;
        font-weight: 700;
    }
    .stPlotlyChart {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
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


def render_metric_card(value, unit, label):
    """Helper to render metric cards with consistent styling"""
    display_value = f"{value}{unit}" if value is not None else "N/A"
    return f"""
                <div class="metric-card">
                    <p class="metric-value">{display_value}</p>
                    <p class="metric-label">{label}</p>
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


# Main app
st.title("Palisades Tahoe Snow Conditions")
st.markdown("### Real-time snow and weather data from USDA SNOTEL Station")

# Fetch and process data
with st.spinner("Loading latest conditions..."):
    try:
        weather_data_json = fetch_weather_data()
        weather_df = process_weather_data(weather_data_json)
        metrics, latest_date = get_latest_metrics(weather_df)

        # Display last update time
        st.caption(f"Last updated: {latest_date.strftime('%B %d, %Y at %I:%M %p')}")

        # Current conditions metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                render_metric_card(metrics.get("SNWD"), '"', "Snow Depth"),
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                render_metric_card(metrics.get("TOBS"), "°F", "Temperature"),
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                render_metric_card(metrics.get("WTEQ"), '"', "Snow Water Equivalent"),
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

        with col1:
            st.metric("Max Snow Depth", f'{stats["max_snow"]:.0f}"')
        with col2:
            st.metric("Avg Snow Depth", f'{stats["avg_snow"]:.1f}"')
        with col3:
            st.metric("Max Temperature", f"{stats['max_temp']:.0f}°F")
        with col4:
            st.metric("Min Temperature", f"{stats['min_temp']:.0f}°F")

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info(
            "Please try refreshing the page. If the problem persists, the USDA API may be temporarily unavailable."
        )

# Footer
st.markdown("---")
st.caption(
    "Data source: USDA Natural Resources Conservation Service SNOTEL Network | Station: Palisades Tahoe (784:CA:SNTL)"
)
