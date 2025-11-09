#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
import numpy as np

def bucket_name(h: int, buckets: list[dict])->str:
    for b in buckets:
        if b["h_start"] <= h <= b["h_end"]:
            return b["name"]
    return "h_na"

def main():
    ap = argparse.ArgumentParser(description="Phase 2 – Step 5: Compute MAE/RMSE by country and global.")
    ap.add_argument("--setup_json", required=True)
    ap.add_argument("--forecasts", nargs="+", required=True)
    ap.add_argument("--out_by_country", required=True)
    ap.add_argument("--out_global", required=True)
    args = ap.parse_args()

    with open(args.setup_json, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    buckets = cfg["buckets"]

    frames = [pd.read_csv(p) for p in args.forecasts]
    fc = pd.concat(frames, ignore_index=True)

    fc["ae"] = (fc["pred_c"] - fc["truth_c"]).abs()
    fc["se"] = (fc["pred_c"] - fc["truth_c"])**2
    fc["bucket"] = fc["horizon"].apply(lambda h: bucket_name(int(h), buckets))

    agg = (fc.groupby(["country","baseline","bucket"])
             .agg(n=("ae","count"), MAE=("ae","mean"), RMSE=("se", lambda s: float(np.sqrt(s.mean()))))
             .reset_index())

    g = (agg.groupby(["baseline","bucket"])
            .agg(countries=("country","nunique"), MAE=("MAE","mean"), RMSE=("RMSE","mean"))
            .reset_index())

    Path(args.out_by_country).parent.mkdir(parents=True, exist_ok=True)
    agg.to_csv(args.out_by_country, index=False)
    g.to_csv(args.out_global, index=False)
    print("[OK] Wrote:", args.out_by_country, "and", args.out_global)

if __name__ == "__main__":
    main()
