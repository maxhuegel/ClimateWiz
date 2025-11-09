# EmissionWiz

EmissionWiz is an interactive 3D globe (Streamlit + Globe.gl/Three.js) to explore yearly warming by country. It supports:

- Anomalies (ΔT) relative to the 1901–2029 country baseline

- Absolute annual temperatures (°C)

- Colorblind palette, PNG export, and a country info panel with a mini trend chart (1901–last year in the data)

Target: education & exploration—quick, intuitive views of climate change across countries and decades.

## Features

- Modes: Anomaly (ΔT) and Absolute (°C)

- Hover: country name; Click: info panel with

  - snapshot value for the currently selected year,

  - linear trend (°C/decade),

  - mini time-series chart (1901–last available year, e.g. 2029)

- Colorblind mode: alternate, daltonism-friendly palette

- Export PNG: save a screenshot of the globe

- Guide: in-app explanation (top-left button)

## Project Structure

```
EmissionWiz/
├─ src/
│  ├─ app/
│  │  └─ app.py                        # Streamlit app embedding Globe.gl (HTML/JS)
│  ├─ data/
│  │  └─ temperature/
│  │     └─ temp_per_country/
│  │        └─ yearly_temp_aggregated/
│  │           └─ country_year.csv     # Annual per-country data (see schema)
└─ ...
```

## Data Schema
`src/data/temperature/temp_per_country/yearly_temp_aggregated/country_year.csv`

Required columns:
- `country` – country name (underscores or spaces are fine; normalized in-app)
- `year` – integer year
- `temp_c` – annual mean temperature (°C)
- `base` – country mean 1901–2029 (°C)
- `anom` – `temp_c - base` (°C)

Example:

```
country,year,temp_c,base,anom
Albania,1901,10.9,12.3,-1.4
Albania,1902,11.8,12.3,-0.5
...
```

The app harmonizes country names (e.g., `Bosnia and Herz.` → `Bosnia-Herzegovinia`) via a JS alias map.

## Installation
```
# Optional: conda env
conda create -n emissionwiz python=3.11 -y
conda activate emissionwiz

pip install streamlit pandas
```

## Run
From the project root:
```
streamlit run src/app/app.py
```
Streamlit will open at `http://localhost:8501`. The app renders in fullscreen.

## How to Use

1) Choose Anomaly or Absolute in the top-right panel.

2) Drag the year slider to select a snapshot year.

3) Click a country to open the info panel (left):
   - snapshot value for the selected year,
   - linear trend (°C/decade) computed over 1901–last available year,
   - mini chart with axes and units.

4) Toggle Colorblind: ON/OFF for an alternative palette.

5) Export PNG saves a screenshot of the globe.

## Years & Slider Behavior

 - The app loads all years present in `country_year.csv` (e.g., 1901–2029 including projections).

- The slider default position is deliberately set to 2024 (or, if absent, the latest available year).
This is controlled in the JS section of app.py:

```js
const START_YEAR = '2024';
```
 - The maximum slider year is computed from the last year in the CSV.
If the slider stops at 2024, the CSV likely does not contain later years or the configured CSV path is wrong.

## Architecture

- Streamlit (Python) loads the CSV with pandas, normalizes names, and builds a JSON payload:
  - `years`: ordered list of years (strings),
  - `values.anom[year][country] `and `values.abs[year][country]`,
  - color clipping ranges for both metrics.

- Streamlit embeds an HTML/JS block with Globe.gl (Three.js) that:
  - renders Earth, country polygons, borders, atmosphere,
  - colors polygons based on the current year & metric,
  - handles click → info panel with a mini SVG chart,
  - provides colorblind mode and PNG export.

### Diagram

```css
country_year.csv
      │
      ▼
  pandas (Streamlit)
      │  payload (years, values, clips, units)
      ▼
 Streamlit iframe → HTML/JS
      ▼
  Globe.gl + UI (buttons, slider, info panel, export)
```

## Configuration

In src/app/app.py:
- CSV path: `DATA_CSV`
- Anomaly color range: `ANOM_CLIP = (-3.0, 3.0)`
- Slider default year: `const START_YEAR = '2024'` (JS)
- Country aliases: `ALIASES` (JS)
- Color schemes: handled in `colorScaleFactory` / `setGradient` (JS)

## Extending

- More years / projections: just extend `country_year.csv`; the app adapts automatically.
- Additional metrics: add new CSV columns and mirror the `anom/abs` pattern in the payload and JS.
- Search / autoplay: the panel design supports extra controls if you want to add them.

## Troubleshooting

- Slider capped at 2024
  - Ensure the CSV actually contains years > 2024; verify `DATA_CSV` path.

- “Missing columns”
  - CSV must include `country, year, temp_c, base, anom.`

- Country appears gray
  - No data for that country or name mismatch—update the `ALIASES` map if needed.

- Layout/frame issues
  - Clear Streamlit cache (`st.cache_data.clear()`), hard-refresh the browser.

## Methodology
- Source: country-aggregated annual means (e.g., CRU TS v4.x based preparation).
- Anomalies: `year_value − mean(1901–2029)` per country.
- Aggregation: monthly → annual means; countries require sufficient monthly coverage.
- Country harmonization: alias map; some small/disputed territories may be excluded.