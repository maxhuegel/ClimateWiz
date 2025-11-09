#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
import pandas as pd
from datetime import datetime

def main():
    app_root = Path(__file__).resolve().parents[1]
    baselines = app_root / "baselines"
    reports = app_root / "reports"
    by_country_path = baselines / "metrics_by_country.csv"
    global_path = baselines / "metrics_global.csv"
    mc = pd.read_csv(by_country_path)
    mg = pd.read_csv(global_path)

    # wins by country
    wins = []
    for bkt, g in mc.groupby("bucket"):
        piv = g.pivot_table(index="country", columns="baseline", values="RMSE", aggfunc="first")
        if {"lag12","climatology"}.issubset(piv.columns):
            cmp = (piv["lag12"] < piv["climatology"])
            wins.append({"bucket": bkt, "wins_lag12_over_clim_share": float(cmp.mean()), "countries": int(cmp.notna().sum())})
    wins_df = pd.DataFrame(wins).sort_values("bucket")

    # topline
    topline = mg.sort_values(["bucket","baseline"]).copy()

    # write quick summary
    lines = [f"# Phase 2 – Quick Summary", f"Date: {datetime.utcnow().isoformat()}Z", ""]
    lines.append("| bucket | baseline | countries | MAE | RMSE |")
    lines.append("|---|---|---:|---:|---:|")
    for _, r in topline.iterrows():
        lines.append(f"| {r['bucket']} | {r['baseline']} | {int(r['countries'])} | {r['MAE']:.3f} | {r['RMSE']:.3f} |")
    lines.append("")
    lines.append("| bucket | countries | share_lag12_better |")
    lines.append("|---|---:|---:|")
    for _, r in wins_df.iterrows():
        lines.append(f"| {r['bucket']} | {int(r['countries'])} | {r['wins_lag12_over_clim_share']:.1%} |")
    (reports / "phase2_quick.md").write_text("\n".join(lines), encoding="utf-8")
    print("[OK] Wrote reports/phase2_quick.md")

if __name__ == "__main__":
    main()
