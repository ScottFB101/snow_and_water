# Copilot Instructions

## Project Overview
Single-file Streamlit dashboard (`tahoe-snow-dashboard.py`) displaying real-time snow and weather data for Palisades Tahoe from the USDA SNOTEL network. No backend, no database — all data is fetched live from a public REST API and processed in memory.

## Running the App
```bash
# Activate venv first (see setup.txt for initial creation)
source .venv/bin/activate       # macOS/Linux
.venv\Scripts\Activate.ps1      # Windows PowerShell

streamlit run tahoe-snow-dashboard.py
```

## Data Source
- **API**: USDA AWDB REST API — `https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data`
- **Station**: Palisades Tahoe `784:CA:SNTL`
- **Elements**: `SNWD` (snow depth, in), `TOBS` (temperature °F), `WTEQ` (SWE, in), `SNDN`, `SNRR`
- **Frequency**: Hourly; `WTEQ` is a daily measurement that gets forward-filled across hours
- **Season start**: Hardcoded `start_date = "2025-10-01"` in `fetch_weather_data()` — **update each October**

## Key Patterns

### Data Processing — use Polars, not pandas
All DataFrame work uses `polars`. Raw API JSON is normalized from long-format → pivoted wide (each element as a column). Snow density is derived: `ρ_s = (1000 × WTEQ) / SNWD` (kg/m³).

```python
# Correct idiom for conditional column
df.with_columns(
    pl.when(condition).then(value).otherwise(None).alias("col")
)
```

### Charting — always use the helpers
All Altair charts must go through `configure_chart()` and `create_axis()` for consistent styling. Colors and font sizes live in `CHART_CONFIG`.

```python
chart = base.mark_area(...).encode(...)
st.altair_chart(configure_chart(chart, "Title", height=400))
```

### Metric Cards — HTML via `unsafe_allow_html`
Metric cards are raw HTML strings rendered through `st.markdown(..., unsafe_allow_html=True)`. Use `render_metric_card()` for current-conditions cards; stat cards use inline `<div class="metric-card">` directly.

### Caching
Both API fetch and data processing are decorated with `@st.cache_data(ttl=3600)`. Do not add stateful side effects inside cached functions.

## CSS / Styling
Tailwind CSS loaded from CDN; custom overrides injected via `st.markdown` at app startup. CSS classes: `.metric-card`, `.metric-value`, `.metric-label`, `.subheader-text`, `.caption-text`. Color palette is sky-blue (`#0369A1`, `#0EA5E9`) on a light gradient background.

## Deployment
Hosted on **Streamlit Cloud**. Changes pushed to `main` are automatically deployed. The `requirements.txt` file is used by Streamlit Cloud to install dependencies — keep it pinned and up to date.

## Dependencies
Pinned in `requirements.txt`. Core: `streamlit`, `polars`, `altair`, `requests`. Install with:
```bash
pip install -r requirements.txt
```

## Known Backlog
These features are planned but not yet implemented (tracked as comments in `tahoe-snow-dashboard.py`):
- **Snow history line/dataframe chart** — a dedicated view for full-season snow depth history
- **Layered temperature chart** — overlay multiple series on the temp tab (reference: [MLB Strikeouts example](https://github.com/jakevdp/altair-examples/blob/master/notebooks/MLB_Strikeouts.ipynb))
- **Heatmap** — visualize Year × Month for a chosen metric (Snow Depth, Temp, etc.)
