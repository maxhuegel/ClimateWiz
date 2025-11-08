# Outlier Policy (Phase 1 – Item 4)

## Purpose
Check outliers to prevent bias in climatology/anomalies and in lag/rolling features.

## Country identifier
We use the **English country name** in a column called `country`. If your data is stored as **one file per country** (e.g., in `src/data/tempPerCountry`), we will derive `country` from the filename.

## Inputs
Two modes are supported:
1) **Single file**: `--input` pointing to a CSV/Parquet/Feather with columns: `country`, `year`, `month`, `temp_c`.
2) **Directory of per‑country files**: `--input_dir` pointing to a folder (e.g., `src/data/tempPerCountry`) that contains one file per country. We infer `country` from the filename (without extension). Each file must contain at least `year`, `month`, `temp_c`.

## Definitions
- **Z-Score (per month type):** Standardization within the same calendar month (compare January only with January).
- **Robust Z:** Median and MAD (1.4826 * MAD as scale).

## Flags
- `flag_abs_range`: |temp_c| > 60 °C
- `flag_jump_gt15`: |temp_c - temp_{prev_month}| > 15 °C (within the same country)
- `flag_z_gt3`: |z| > 3 (classic)
- `flag_zrob_gt4`: |z_robust| > 4 (robust)
- `flag_any_outlier`: OR across all flags above

## Procedure
1. Ensure columns: `country`, `year`, `month`, `temp_c` (if directory mode is used, we add `country` from the filename).
2. Group by (`country`, `month`) and compute:
   - classic mean µ and std σ → `z`
   - median and MAD → `z_robust = (x - median) / (1.4826 * MAD)`
3. Sort per country chronologically and compute month-to-month differences → `flag_jump_gt15`.
4. Write enriched dataset + aggregation report.

## Removal vs. Retention
- **Do not delete automatically.** Only fix obvious typos.
- **Document** all flags and consider them during modelling (e.g., as weights or explicit exclusion rule depending on share).

## Parameters (recommended, adjustable)
- Thresholds: 60 °C, 15 °C, |z|>3, |z_robust|>4.
- Required columns: `country`, `year`, `month`, `temp_c`.
- Input formats: Parquet/CSV/Feather.

## Outputs
- `data_clean/monthly_with_outlier_flags.parquet|csv`
- `reports/outliers_summary.csv` (counts per country + share)
- `reports/outliers_summary.json` (metadata, parameters, timestamp)
## Usage

You can run the script either on a single consolidated file or on a directory that contains one file per country.

### Single file
Input file must contain these columns: `country, year, month, temp_c` (optionally `date`).

```
python scripts/qa_outliers.py   --input data_clean/monthly_clean.csv   --output data_clean/monthly_with_outlier_flags.csv   --summary_csv reports/outliers_summary.csv   --summary_json reports/outliers_summary.json
```

### Directory with one file per country
Each file must contain at least: `year, month, temp_c` and preferably `country`.  
If `country` is missing, it is derived from the **filename** (without extension).  
If `year`/`month` are missing but `date` exists, they are extracted from `date`.

```
python scripts/qa_outliers.py   --input_dir src/data/tempPerCountry   --output data_clean/monthly_with_outlier_flags.csv   --summary_csv reports/outliers_summary.csv   --summary_json reports/outliers_summary.json
```

### Parameters (common)
- `--country_col`, `--year_col`, `--month_col`, `--temp_col` to override column names if needed.
- `--abs_temp_limit` (default 60.0), `--jump_threshold` (default 15.0),
  `--z_thresh` (default 3.0), `--zrob_thresh` (default 4.0).

### Outputs
- **Flagged dataset** (`--output`): original rows + z, z_robust and all boolean flags.
- **Summary CSV** (`--summary_csv`): per-country counts and percentages for each flag and overall.
- **Summary JSON** (`--summary_json`): metadata (parameters, timestamp, row counts).

### Notes
- Parquet requires `pyarrow` or `fastparquet`; CSV works out of the box.
- Run from the project root (`EmissionWiz/EmissionWiz`) so relative paths resolve.
- In PyCharm, set *Script path* to `scripts/qa_outliers.py` and *Working directory* to the project root.
