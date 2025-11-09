# Phase 2 – Summary (Step 8)
Date: 2025-11-09T03:00:20.455159Z

## Setup
- Rolling-origin cutoffs from `reports/phase2_cutoffs.csv`
- Horizons: 1–60 months; Buckets: 1–3, 4–6, 7–12, 13–24, 25–60
- Baselines: climatology (anomaly=0) and seasonal-naive lag12 (on anomalies)

## Global topline (RMSE by bucket)

| bucket | best_baseline | RMSE | MAE |
|---|---|---:|---:|
| h01_03 | climatology | 1.083 | 0.858 |
| h04_06 | climatology | 0.809 | 0.655 |
| h07_12 | climatology | 0.938 | 0.731 |
| h13_24 | climatology | 0.954 | 0.745 |
| h25_60 | climatology | 0.955 | 0.745 |

## Wins by country (lag12 vs climatology)

| bucket | countries | share_lag12_better |
|---|---:|---:|
| h01_03 | 291 | 26.8% |
| h04_06 | 291 | 39.5% |
| h07_12 | 291 | 26.1% |

## Notes
- Gaps for lag12 are expected if the source month (t−12) is not available before the cutoff (this is correct).
- Forecasts and metrics strictly avoid leakage (only past data relative to the cutoff).
- For any bucket with low coverage, consider regenerating Step 1 with smaller `--horizons_max` (e.g., 36).