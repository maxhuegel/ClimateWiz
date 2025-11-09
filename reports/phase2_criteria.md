# Phase 2 – Go/No-Go criteria (Step 7)

Date: 2025-11-09T03:00:20.450492Z

**Thresholds for proceeding to Phase 3 models:**

1. The learned model must beat **both baselines** (climatology and lag12) in **≥ 70%** of countries **per bucket** for 1–12 and 13–24 months.
2. Achieve a **global RMSE improvement ≥ 10–15%** over the **better baseline** in the buckets **1–12** and **13–24** months.
3. No catastrophic regressions: In **no more than 10%** of countries may the model underperform the better baseline by **> 10% RMSE** in any bucket.

These thresholds are to be checked using the same **rolling-origin** setup and the same **truth/pred** reconstruction (°C = anomaly + climatology).
