#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

DEFAULTS = dict(
    country_col="country",          # use English country names
    year_col="year",
    month_col="month",
    temp_col="temp_c",
    abs_temp_limit=60.0,
    jump_threshold=15.0,
    z_thresh=3.0,
    zrob_thresh=4.0,
)

def robust_scale(series: pd.Series) -> pd.Series:
    med = series.median()
    mad = (series - med).abs().median()
    scale = 1.4826 * mad if mad > 0 else np.nan
    if scale and not np.isnan(scale):
        return (series - med) / scale
    return pd.Series([np.nan] * len(series), index=series.index)

def classic_z(series: pd.Series) -> pd.Series:
    mu = series.mean()
    sigma = series.std(ddof=1)
    if sigma and not np.isnan(sigma) and sigma > 0:
        return (series - mu) / sigma
    return pd.Series([np.nan] * len(series), index=series.index)

def add_outlier_flags(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    c, y, m, t = cfg["country_col"], cfg["year_col"], cfg["month_col"], cfg["temp_col"]
    df = df.copy()
    df = df.sort_values([c, y, m]).reset_index(drop=True)

    # Absolute range flag
    df["flag_abs_range"] = df[t].abs() > cfg["abs_temp_limit"]

    # Group by (country, month) for z-scores
    grp = df.groupby([c, m], dropna=False)[t]
    df["z"] = grp.transform(classic_z)
    df["z_robust"] = grp.transform(robust_scale)
    df["flag_z_gt3"] = df["z"].abs() > cfg["z_thresh"]
    df["flag_zrob_gt4"] = df["z_robust"].abs() > cfg["zrob_thresh"]

    # Month-to-month jump within country
    df["temp_prev"] = df.groupby(c)[t].shift(1)
    df["flag_jump_gt15"] = (df[t] - df["temp_prev"]).abs() > cfg["jump_threshold"]

    # Combined
    df["flag_any_outlier"] = df[["flag_abs_range","flag_jump_gt15","flag_z_gt3","flag_zrob_gt4"]].any(axis=1)

    return df

def summarize_flags(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    c = cfg["country_col"]
    total = df.groupby(c, dropna=False).size().rename("n_rows")
    flagged = df.groupby(c, dropna=False)["flag_any_outlier"].sum().rename("n_flagged")
    out = pd.concat([total, flagged], axis=1)
    out["pct_flagged"] = (out["n_flagged"] / out["n_rows"]).round(4)
    for col in ["flag_abs_range","flag_jump_gt15","flag_z_gt3","flag_zrob_gt4"]:
        out[col] = df.groupby(c, dropna=False)[col].sum()
    return out.reset_index()

def load_dataset(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".feather":
        return pd.read_feather(path)
    raise ValueError(f"Unsupported input format: {suffix}")

def save_df(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".parquet":
        df.to_parquet(path, index=False)
    elif path.suffix.lower() == ".csv":
        df.to_csv(path, index=False)
    else:
        raise ValueError("Output must be .parquet or .csv")


def load_from_dir(input_dir: Path, cfg: dict) -> pd.DataFrame:
    """Read all supported files in a directory. If column `country` exists, use it; otherwise infer from filename (stem).
    If `year`/`month` are missing but `date` exists, extract them."""
    files = []
    for p in input_dir.iterdir():
        if p.is_file() and p.suffix.lower() in {".csv", ".parquet", ".feather"}:
            files.append(p)
    if not files:
        raise SystemExit(f"No data files found in {input_dir}")
    frames = []
    for p in files:
        df = load_dataset(p).copy()

        # Ensure country column
        if cfg["country_col"] in df.columns:
            pass  # use as-is
        else:
            df[cfg["country_col"]] = p.stem  # derive from filename

        # Ensure year/month columns (extract from date if needed)
        if cfg["year_col"] not in df.columns or cfg["month_col"] not in df.columns:
            if "date" in df.columns:
                # try to parse year/month from date
                dt = pd.to_datetime(df["date"], errors="coerce")
                if cfg["year_col"] not in df.columns:
                    df[cfg["year_col"]] = dt.dt.year
                if cfg["month_col"] not in df.columns:
                    df[cfg["month_col"]] = dt.dt.month
            else:
                missing = [x for x in [cfg["year_col"], cfg["month_col"]] if x not in df.columns]
                raise SystemExit(f"Required columns missing in {p.name}: {missing} (and no 'date' column to derive from)")

        # Ensure temp column present
        if cfg["temp_col"] not in df.columns:
            raise SystemExit(f"Required column '{cfg['temp_col']}' missing in {p.name}")

        # Keep only necessary columns
        keep_cols = [cfg["country_col"], cfg["year_col"], cfg["month_col"], cfg["temp_col"]]
        frames.append(df[keep_cols])

    return pd.concat(frames, ignore_index=True)
def main():
    p = argparse.ArgumentParser(description="Phase 1 – Item 4: Outlier flags for monthly data (supports per-country directory input).")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--input", help="Path to single monthly dataset (parquet/csv) with columns: country, year, month, temp_c")
    g.add_argument("--input_dir", help="Path to directory with one file per country (e.g., src/data/tempPerCountry). Country is derived from filename.")
    p.add_argument("--output", required=True, help="Output file (.parquet or .csv) with outlier flags")
    p.add_argument("--summary_csv", required=True, help="Aggregation report per country (.csv)")
    p.add_argument("--summary_json", required=True, help="Metadata/parameters (.json)")

    p.add_argument("--country_col", default=DEFAULTS["country_col"])
    p.add_argument("--year_col", default=DEFAULTS["year_col"])
    p.add_argument("--month_col", default=DEFAULTS["month_col"])
    p.add_argument("--temp_col", default=DEFAULTS["temp_col"])
    p.add_argument("--abs_temp_limit", type=float, default=DEFAULTS["abs_temp_limit"])
    p.add_argument("--jump_threshold", type=float, default=DEFAULTS["jump_threshold"])
    p.add_argument("--z_thresh", type=float, default=DEFAULTS["z_thresh"])
    p.add_argument("--zrob_thresh", type=float, default=DEFAULTS["zrob_thresh"])

    args = p.parse_args()
    cfg = dict(
        country_col=args.country_col,
        year_col=args.year_col,
        month_col=args.month_col,
        temp_col=args.temp_col,
        abs_temp_limit=args.abs_temp_limit,
        jump_threshold=args.jump_threshold,
        z_thresh=args.z_thresh,
        zrob_thresh=args.zrob_thresh,
    )

    if args.input_dir:
        df = load_from_dir(Path(args.input_dir), cfg)
    else:
        df = load_dataset(Path(args.input))

    # basic column checks
    required = [cfg["country_col"], cfg["year_col"], cfg["month_col"], cfg["temp_col"]]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns: {missing}. Available: {list(df.columns)}")

    df_flags = add_outlier_flags(df, cfg)
    save_df(df_flags, Path(args.output))

    summary = summarize_flags(df_flags, cfg)
    Path(args.summary_csv).parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary_csv, index=False)

    meta = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input": args.input if args.input else args.input_dir,
        "output": args.output,
        "summary_csv": args.summary_csv,
        "params": cfg,
        "rowcount_input": int(len(df)),
        "rowcount_output": int(len(df_flags)),
        "n_flagged_total": int(df_flags["flag_any_outlier"].sum()),
    }
    with open(args.summary_json, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"[OK] Flags written to: {args.output}")
    print(f"[OK] Summary: {args.summary_csv}")
    print(json.dumps(meta, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
