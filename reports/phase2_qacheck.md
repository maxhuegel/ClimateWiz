# Phase 2 – QA check (Step 6)
Date: 2025-11-09T03:00:20.451119Z

## Global topline (RMSE/MAE by baseline × bucket)

| bucket | baseline | countries | MAE | RMSE |
|---|---|---:|---:|---:|
| h01_03 | climatology | 291 | 0.858 | 1.083 |
| h01_03 | lag12 | 291 | 0.975 | 1.269 |
| h04_06 | climatology | 291 | 0.655 | 0.809 |
| h04_06 | lag12 | 291 | 0.650 | 0.846 |
| h07_12 | climatology | 291 | 0.731 | 0.938 |
| h07_12 | lag12 | 291 | 0.796 | 1.068 |
| h13_24 | climatology | 291 | 0.745 | 0.954 |
| h25_60 | climatology | 291 | 0.745 | 0.955 |

## Wins by country (lag12 better than climatology)

| bucket | countries | share_lag12_better |
|---|---:|---:|
| h01_03 | 291 | 26.8% |
| h04_06 | 291 | 39.5% |
| h07_12 | 291 | 26.1% |

## Notable underperformers (lag12 worse than climatology – largest RMSE deltas)

| bucket | country | delta_rmse |
|---|---|---:|
| h01_03 | Uzbekistan | 0.961 |
| h01_03 | Finland | 0.927 |
| h01_03 | Turkmenistan | 0.883 |
| h01_03 | Kyrgyzstan | 0.857 |
| h01_03 | Kosovo | 0.851 |
| h01_03 | Serbia | 0.851 |
| h01_03 | Romania | 0.837 |
| h01_03 | Hungary | 0.835 |
| h01_03 | Austria | 0.827 |
| h01_03 | Wrangel_Isl | 0.822 |
| h04_06 | Paraguay | 0.654 |
| h04_06 | Uruguay | 0.593 |
| h04_06 | Belarus | 0.567 |
| h04_06 | Lithuania | 0.553 |
| h04_06 | Estonia | 0.538 |
| h04_06 | Latvia | 0.530 |
| h04_06 | Finland | 0.498 |
| h04_06 | South_Georgia | 0.478 |
| h04_06 | Argentina | 0.477 |
| h04_06 | Denmark | 0.456 |
| h07_12 | Finland | 0.909 |
| h07_12 | Estonia | 0.751 |
| h07_12 | Moldova | 0.712 |
| h07_12 | Belarus | 0.675 |
| h07_12 | Sweden | 0.665 |
| h07_12 | Romania | 0.663 |
| h07_12 | Lithuania | 0.659 |
| h07_12 | Ukraine | 0.657 |
| h07_12 | Latvia | 0.637 |
| h07_12 | Norway | 0.631 |