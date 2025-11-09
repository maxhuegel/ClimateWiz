#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from datetime import datetime

FREQS = {"yearly": 12, "quarterly": 3}

def load_df(path: Path)->pd.DataFrame:
    if path.suffix.lower()==".csv": return pd.read_csv(path)
    if path.suffix.lower()==".parquet": return pd.read_parquet(path)
    raise SystemExit(f"Unsupported file extension: {path.suffix}")

def main():
    ap = argparse.ArgumentParser(description="Phase 2 – Step 1: Define cutoffs, horizons, buckets.")
    ap.add_argument("--anomalies", required=True)
    ap.add_argument("--cutoff_freq", choices=["yearly","quarterly"], default="yearly")
    ap.add_argument("--horizons_max", type=int, default=60)
    ap.add_argument("--min_history_months", type=int, default=24)
    ap.add_argument("--output_cutoffs", required=True)
    ap.add_argument("--output_json", required=True)
    args = ap.parse_args()

    df = load_df(Path(args.anomalies))
    req = {"country","year","month","anomaly_c","clim_temp_c","temp_c"}
    miss = [c for c in req if c not in df.columns]
    if miss: raise SystemExit(f"Missing columns in anomalies: {miss}")

    df["_k"] = df["year"].astype(int)*12 + (df["month"].astype(int)-1)
    kmin, kmax = int(df["_k"].min()), int(df["_k"].max())
    step = FREQS[args.cutoff_freq]

    # candidate cutoffs that have min history before and horizons_max after globally
    candidates = list(range(kmin + args.min_history_months, kmax - args.horizons_max + 1, step))

    # per-country coverage window
    per_country = df.groupby("country")["_k"].agg(["min","max"]).rename(columns={"min":"kmin","max":"kmax"}).reset_index()

    rows = []
    for k in candidates:
        hist_ok = (k - per_country["kmin"]) >= args.min_history_months
        fut_ok  = (per_country["kmax"] - k) >= args.horizons_max
        both_ok = hist_ok & fut_ok
        y, m = k//12, (k%12)+1
        rows.append({
            "cutoff_ym": f"{y:04d}-{m:02d}",
            "cutoff_key": int(k),
            "countries_total": int(len(per_country)),
            "share_with_history_ok": float(hist_ok.mean()),
            "share_with_future_ok": float(fut_ok.mean()),
            "share_with_both_ok": float(both_ok.mean())
        })
    pd.DataFrame(rows).to_csv(args.output_cutoffs, index=False)

    buckets = [
        {"name":"h01_03","h_start":1,"h_end":3},
        {"name":"h04_06","h_start":4,"h_end":6},
        {"name":"h07_12","h_start":7,"h_end":12},
        {"name":"h13_24","h_start":13,"h_end":24},
        {"name":"h25_60","h_start":25,"h_end":args.horizons_max},
    ]
    meta = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "anomalies": str(args.anomalies),
        "cutoff_freq": args.cutoff_freq,
        "horizons_max": int(args.horizons_max),
        "min_history_months": int(args.min_history_months),
        "buckets": buckets,
        "note": "Pick cutoffs where share_with_both_ok ≥ 0.7 as a rule of thumb."
    }
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("[OK] Wrote:", args.output_cutoffs, "and", args.output_json)

if __name__ == "__main__":
    main()
