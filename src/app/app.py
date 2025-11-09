# app.py
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html

DATA_CSV = Path("src/data/temperature/temp_per_country/yearly_temp_aggregated/country_year.csv")
ANOM_CLIP = (-3.0, 3.0)

st.set_page_config(page_title="EmissionWiz", page_icon="🌍", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
:root, html, body { margin:0; padding:0; height:100%; overflow:hidden; background:#000; }
#MainMenu, header, footer { display:none !important; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stSidebar"], [data-testid="stSidebarNav"], [data-testid="collapsedControl"] { display:none !important; }
[data-testid="stAppViewContainer"] { padding:0 !important; overflow:hidden !important; }
.block-container { padding:0 !important; margin:0 !important; max-width:100% !important; }
[data-testid="stIFrame"]        { position:fixed !important; inset:0 !important; width:100vw !important; height:100vh !important; border:none !important; border-radius:0 !important; box-shadow:none !important; }
[data-testid="stIFrame"] iframe { width:100vw !important; height:100vh !important; display:block; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_payload(csv_path: Path) -> dict:
    df = pd.read_csv(csv_path)
    req = {"country", "year", "temp_c", "base", "anom"}
    missing = req - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {csv_path}: {missing}")
    df["country_norm"] = (df["country"].astype(str).str.replace("_", " ", regex=False).str.strip())
    years = sorted(df["year"].dropna().astype(int).unique().tolist())
    years_str = [str(y) for y in years]
    values_anom, values_abs = {}, {}
    for y in years:
        sub = df[df["year"] == y]
        values_anom[str(y)] = {c: float(v) for c, v in zip(sub["country_norm"], sub["anom"].round(3))}
        values_abs[str(y)] = {c: float(v) for c, v in zip(sub["country_norm"], sub["temp_c"].round(2))}
    q1, q99 = df["temp_c"].quantile([0.01, 0.99]).tolist()
    abs_clip = (float(round(q1, 1)), float(round(q99, 1)))
    return {
        "years": years_str,
        "values": {"anom": values_anom, "abs": values_abs},
        "clips": {"anom": ANOM_CLIP, "abs": abs_clip},
        "units": {"anom": "ΔT (°C vs 1991–2020)", "abs": "Temperature (°C)"},
        "default_metric": "anom"
    }

payload = load_payload(DATA_CSV)
PAYLOAD_JSON = json.dumps(payload)

HTML = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  html,body{margin:0; padding:0; height:100vh; background:#000; overflow:hidden}
  #root{position:fixed; inset:0; background:#000;}
  .panel{
    position: fixed; top:16px; right:16px; z-index: 9999;
    background: rgba(0,0,0,.45); color:#fff; padding:10px 12px; border-radius:10px;
    font: 12px/1.35 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
    border:1px solid rgba(255,255,255,.2); backdrop-filter: blur(3px);
  }
  .panel button{background:rgba(255,255,255,.12); color:#fff; border:1px solid rgba(255,255,255,.25); border-radius:8px; padding:6px 10px; cursor:pointer}
  .panel button.active{background:#fff; color:#000}
  .grad{width:220px; height:10px; background:linear-gradient(90deg,#2b6cff,#ffffff,#ff2b2b); margin:6px 0 4px;}
  #range{width:220px;}
  #sel{margin-top:4px; font-weight:600;}
</style>
<script src="https://unpkg.com/three@0.155.0/build/three.min.js"></script>
<script src="https://unpkg.com/globe.gl@2.33.1/dist/globe.gl.min.js"></script>
</head>
<body>
<div id="root"></div>
<div class="panel">
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px">
    <button id="btn-anom">Anomaly</button>
    <button id="btn-abs">Absolute</button>
  </div>
  <div><b id="unit">__UNIT__</b></div>
  <div class="grad"></div>
  <div style="display:flex;justify-content:space-between">
    <span id="minlbl">__MIN__</span><span id="maxlbl">__MAX__</span>
  </div>
  <input id="range" type="range" min="0" max="__MAXIDX__" value="__MAXIDX__" />
  <div id="sel"></div>
</div>

<script>
  const PAYLOAD = __PAYLOAD__;
  const YEARS   = PAYLOAD.years;
  const VALUES  = PAYLOAD.values;
  const CLIPS   = PAYLOAD.clips;
  const UNITS   = PAYLOAD.units;

  const ALIASES = {
    "United States of America": "USA",
    "W. Sahara": "Western Sahara",
    "Dem. Rep. Congo": "DR Congo",
    "Dominican Rep.": "Dominican Republic",
    "Falkland Is.": "Falkland Isl",
    "Fr. S. Antarctic Lands": "French Southern Territories",
    "Timor-Leste": "East Timor",
    "Puerto Rico": "Puerto Rico",
    "Côte d'Ivoire": "Ivory Coast",
    "Central African Rep.": "Central African Rep",
    "Eq. Guinea": "Equatorial Guinea",
    "eSwatini": "Swaziland",
    "Palestine": "Palestine",
    "Vanuatu": "Vanatu",
    "Solomon Is.": "Solomon Isl",
    "Taiwan": "Taiwan",
    "Czechia": "Czech Republic",
    "Bosnia and Herz.": "Bosnia-Herzegovinia",
    "North Macedonia": "Macedonia",
    "S. Sudan": "South Sudan",
    "Antarctica": null,
    "N. Cyprus": null,
    "Somaliland": null,
    "French Southern Territories": null
  };

  function csvName(neName) {
    const raw = String(neName || "").trim();
    const a = Object.prototype.hasOwnProperty.call(ALIASES, raw) ? ALIASES[raw] : raw;
    if (a === null) return null;
    return a.replaceAll("_"," ").replaceAll(".","").trim();
  }

  function getValue(map, key){
    if (!key) return null;
    if (key in map) return map[key];
    const space = key.replaceAll("-", " ");
    if (space in map) return map[space];
    const hyph  = key.replaceAll(" ", "-");
    if (hyph in map) return map[hyph];
    return null;
  }

  function colorScaleFactory(m){
    const MIN = CLIPS[m][0], MAX = CLIPS[m][1];
    return function(v){
      if (v==null || isNaN(v)) return 'rgba(120,120,120,0.10)';
      const x = Math.max(MIN, Math.min(MAX, v));
      const t = (x - MIN) / (MAX - MIN);
      const r = t<0.5 ? 2*t*255 : 255;
      const g = t<0.5 ? 2*t*255 : 2*(1-t)*255;
      const b = t<0.5 ? 255 : 2*(1-t)*255;
      return `rgba(${r|0},${g|0},${b|0},0.35)`;
    }
  }

  const DAY_TEX  = 'https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg';
  const BUMP_TEX = 'https://unpkg.com/three-globe/example/img/earth-topology.png';
  const BG_TEX   = 'https://unpkg.com/three-globe/example/img/night-sky.png';

  const globe = Globe({ rendererConfig: { antialias: true, alpha: true, logarithmicDepthBuffer: true } })(document.getElementById('root'))
    .globeImageUrl(DAY_TEX)
    .bumpImageUrl(BUMP_TEX)
    .backgroundImageUrl(BG_TEX)
    .showAtmosphere(true)
    .atmosphereColor('#88ccff')
    .atmosphereAltitude(0.18)
    .width(window.innerWidth)
    .height(window.innerHeight);

  globe.renderer().setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  globe.controls().autoRotate = false;
  globe.controls().autoRotateSpeed = 0.0;
  globe.controls().addEventListener('start', () => globe.controls().autoRotate = false);
  globe.controls().addEventListener('end',   () => globe.controls().autoRotate = true);

  let metric = PAYLOAD.default_metric || "anom";
  let idx = YEARS.length - 1;
  let valueMap = VALUES[metric][YEARS[idx]] || {};
  let colorScale = colorScaleFactory(metric);

  function updateLegend(){
    document.getElementById('unit').textContent = UNITS[metric];
    const [MIN, MAX] = CLIPS[metric];
    document.getElementById('minlbl').textContent = MIN.toString();
    document.getElementById('maxlbl').textContent = MAX.toString();
    document.getElementById('btn-anom').classList.toggle('active', metric==='anom');
    document.getElementById('btn-abs').classList.toggle('active',  metric==='abs');
  }

  fetch('https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson')
    .then(r => r.json())
    .then(geo => {
      globe
        .polygonsData(geo.features)
        .polygonAltitude(0.003)
        .polygonSideColor(() => 'rgba(0,0,0,0)')
        .polygonStrokeColor(() => 'rgba(255,255,255,55)')
        .polygonCapColor(({properties}) => {
          const k = csvName(properties.NAME);
          const v = getValue(valueMap, k);
          return colorScale(v);
        })
        .polygonLabel(({properties}) => {
          const shown = String(properties.NAME || "");
          const k = csvName(properties.NAME);
          const v = getValue(valueMap, k);
          return v!=null ? `${shown}\n${UNITS[metric]}: ${v.toFixed(metric==='anom'?2:1)}` : `${shown}\n(no data)`;
        })
        .polygonsTransitionDuration(0);
      try {
        const csvNames = new Set(Object.keys(valueMap || {}));
        const missing = geo.features.map(f => csvName(f.properties.NAME)).filter(n => n && !csvNames.has(n));
        console.warn('Missing countries (no data from CSV):', missing.length, missing);
      } catch(e) {}
    });

  function applyYear(newIdx){
    idx = Math.max(0, Math.min(YEARS.length-1, newIdx));
    const key = YEARS[idx];
    valueMap = VALUES[metric][key] || {};
    document.getElementById('sel').textContent = key;
    globe
      .polygonCapColor(({properties}) => {
        const k = csvName(properties.NAME);
        const v = getValue(valueMap, k);
        return colorScale(v);
      })
      .polygonLabel(({properties}) => {
        const shown = String(properties.NAME || "");
        const k = csvName(properties.NAME);
        const v = getValue(valueMap, k);
        return v!=null ? `${shown}\n${UNITS[metric]}: ${v.toFixed(metric==='anom'?2:1)}` : `${shown}\n(no data)`;
      });
  }

  function applyMetric(newMetric){
    metric = newMetric;
    colorScale = colorScaleFactory(metric);
    updateLegend();
    applyYear(idx);
  }

  document.getElementById('unit').textContent = UNITS[metric];
  document.getElementById('btn-anom').onclick = () => applyMetric('anom');
  document.getElementById('btn-abs').onclick  = () => applyMetric('abs');
  updateLegend();
  applyYear(idx);
  document.getElementById('range').addEventListener('input', (e) => applyYear(parseInt(e.target.value,10)));

  window.addEventListener('resize', () => {
    globe.width(window.innerWidth); globe.height(window.innerHeight);
  });
</script>
</body>
</html>
"""

html(
    HTML.replace("__PAYLOAD__", PAYLOAD_JSON)
        .replace("__UNIT__", payload["units"][payload["default_metric"]])
        .replace("__MIN__", str(payload["clips"][payload["default_metric"]][0]))
        .replace("__MAX__", str(payload["clips"][payload["default_metric"]][1]))
        .replace("__MAXIDX__", str(len(payload["years"]) - 1)),
    height=10,
    scrolling=False
)
