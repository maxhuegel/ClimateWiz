#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

def load_df(path: Path)->pd.DataFrame:
    if path.suffix.lower()==".csv": return pd.read_csv(path)
    if path.suffix.lower()==".parquet": return pd.read_parquet(path)
    raise SystemExit(f"Unsupported file extension: {path.suffix}")

def key_to_ym(k:int)->tuple[int,int]:
    return k//12, (k%12)+1

def build_lookup(df: pd.DataFrame):
    df = df.copy()
    df["k"] = df["year"].astype(int)*12 + (df["month"].astype(int)-1)
    return df.set_index(["country","k"]).sort_index()

def main():
    ap = argparse.ArgumentParser(description="Phase 2 – Steps 3&4: Generate baseline forecasts (climatology, lag12).")
    ap.add_argument("--anomalies", required=True)
    ap.add_argument("--cutoffs_csv", required=True)
    ap.add_argument("--setup_json", required=True)
    ap.add_argument("--out_climatology", required=True)
    ap.add_argument("--out_lag12", required=True)
    args = ap.parse_args()

    anom = load_df(Path(args.anomalies))
    cutoffs = pd.read_csv(args.cutoffs_csv)
    with open(args.setup_json, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    HMAX = int(cfg["horizons_max"])

    req = {"country","year","month","temp_c","clim_temp_c","anomaly_c"}
    miss = [c for c in req if c not in anom.columns]
    if miss: raise SystemExit(f"Missing columns in anomalies: {miss}")

    L = build_lookup(anom)
    countries = anom["country"].unique().tolist()

    rows_clim, rows_l12 = [], []
    for _, row in cutoffs.iterrows():
        k = int(row["cutoff_key"]); cutoff_ym = row["cutoff_ym"]
        for country in countries:
            for h in range(1, HMAX+1):
                k_tgt = k + h
                y_tgt, m_tgt = key_to_ym(k_tgt)
                # need target truth & climatology
                try:
                    clim_temp = L.loc[(country, k_tgt), "clim_temp_c"]
                    truth_c   = L.loc[(country, k_tgt), "temp_c"]
                except KeyError:
                    continue
                # climatology baseline
                rows_clim.append({
                    "country": country, "year": y_tgt, "month": m_tgt,
                    "cutoff_ym": cutoff_ym, "horizon": h,
                    "pred_c": float(clim_temp), "truth_c": float(truth_c),
                    "baseline": "climatology"
                })
                # lag12 baseline (on anomalies); requires source in history
                k_src = k_tgt - 12
                if k_src <= k:
                    try:
                        src_anom = L.loc[(country, k_src), "anomaly_c"]
                    except KeyError:
                        continue
                    rows_l12.append({
                        "country": country, "year": y_tgt, "month": m_tgt,
                        "cutoff_ym": cutoff_ym, "horizon": h,
                        "pred_c": float(src_anom + clim_temp), "truth_c": float(truth_c),
                        "baseline": "lag12"
                    })

    Path(args.out_climatology).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_lag12).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows_clim).to_csv(args.out_climatology, index=False)
    pd.DataFrame(rows_l12).to_csv(args.out_lag12, index=False)
    print("[OK] Wrote:", args.out_climatology, "and", args.out_lag12)

if __name__ == "__main__":
    main()
