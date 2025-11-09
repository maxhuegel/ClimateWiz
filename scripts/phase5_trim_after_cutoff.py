#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Trim country CSVs from a given cutoff onward.

Schema erwartet (pro Datei): date, year, month, temp_c, country
Standardmodus: löscht alle Zeilen mit (year,month) > cutoff_ym (Cutoff bleibt erhalten).
Optionaler Modus: löscht alle Zeilen mit (year,month) >= cutoff_ym (Cutoff wird mit gelöscht).

Beispiele:
  # 1) Nur Zukunft ab 2025-01 löschen (Cutoff 2024-12 wird behalten)
  python scripts/phase5_trim_after_cutoff.py \
    --country_dir src/data/temperature/temp_per_country \
    --cutoff_ym 2024-12 \
    --out_dir src/data/temperature/temp_per_country_trimmed

  # 2) Alles ab inkl. 2024-12 löschen
  python scripts/phase5_trim_after_cutoff.py \
    --country_dir src/data/temperature/temp_per_country \
    --cutoff_ym 2024-12 \
    --out_dir src/data/temperature/temp_per_country_trimmed \
    --drop_from_cutoff

  # 3) In place überschreiben (Vorsicht!)
  python scripts/phase5_trim_after_cutoff.py \
    --country_dir src/data/temperature/temp_per_country \
    --cutoff_ym 2024-12 \
    --out_dir src/data/temperature/temp_per_country \
    --drop_from_cutoff
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

REQ = {"date","year","month","temp_c","country"}

def ym_to_key(ym: str) -> int:
    y, m = ym.split("-")
    return int(y)*12 + int(m) - 1

def main():
    ap = argparse.ArgumentParser(description="Delete rows from cutoff onward in per-country CSVs.")
    ap.add_argument("--country_dir", required=True, help="Folder with country CSVs")
    ap.add_argument("--cutoff_ym",   required=True, help="YYYY-MM (e.g., 2024-12)")
    ap.add_argument("--out_dir",     required=True, help="Output folder (can be same as input to overwrite)")
    ap.add_argument("--drop_from_cutoff", action="store_true",
                    help="If set, drop rows with ym >= cutoff (default: drop only ym > cutoff)")
    ap.add_argument("--dry_run", action="store_true", help="Report only, write nothing")
    args = ap.parse_args()

    indir  = Path(args.country_dir)
    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    k_cut = ym_to_key(args.cutoff_ym)
    cmp_desc = ">= cutoff" if args.drop_from_cutoff else "> cutoff"

    total_drop = 0
    total_keep = 0
    files = sorted(indir.glob("*.csv"))
    if not files:
        print(f"[WARN] no CSV files in {indir}")
        return

    print(f"[INFO] trimming files in {indir}")
    print(f"[INFO] cutoff_ym = {args.cutoff_ym}  -> key={k_cut}  (dropping rows {cmp_desc})")
    print(f"[INFO] out_dir   = {outdir}   dry_run={args.dry_run}")

    for p in files:
        try:
            df = pd.read_csv(p)
        except Exception as e:
            print(f"[WARN] {p.name}: cannot read ({e}); skip")
            continue

        if not REQ.issubset(df.columns):
            print(f"[WARN] {p.name}: unexpected schema; skip")
            continue

        if df.empty:
            print(f"[OK]   {p.name}: empty (no change)")
            continue

        # build key and mask
        y = df["year"].astype(int)
        m = df["month"].astype(int)
        k = y*12 + (m-1)

        if args.drop_from_cutoff:
            mask_keep = k < k_cut
        else:
            mask_keep = k <= k_cut

        kept = df[mask_keep].copy()
        dropped = len(df) - len(kept)
        total_drop += dropped
        total_keep += len(kept)

        if args.dry_run:
            print(f"[DRY]  {p.name}: dropped={dropped}, kept={len(kept)}")
            continue

        dest = outdir / p.name
        kept.to_csv(dest, index=False)
        print(f"[OK]   {p.name}: dropped={dropped}, kept={len(kept)} -> {dest}")

    print(f"[DONE] files={len(files)} total_dropped={total_drop} total_kept={total_keep}")

if __name__ == "__main__":
    main()