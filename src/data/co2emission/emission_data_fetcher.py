import argparse
import os
import re
import sys
import zipfile
from pathlib import Path

import requests

try:
    import pandas as pd
except Exception:
    pd = None

ENDPOINT = "https://datas.carbonmonitor.org/API/downloadFullDataset.php?source=carbon_global"


def filename_from_headers(resp, fallback):
    cd = resp.headers.get("Content-Disposition", "")
    m = re.search(r'filename="?([^";]+)"?', cd)
    if m:
        return m.group(1)
    return fallback


def download(url: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        ctype = (r.headers.get("Content-Type") or "").lower()
        default_name = "carbon_monitor_download"
        if "zip" in ctype:
            fname = filename_from_headers(r, default_name + ".zip")
        elif "csv" in ctype or "text/plain" in ctype:
            fname = filename_from_headers(r, default_name + ".csv")
        else:
            fname = os.path.basename(url) or default_name + ".bin"
        out_path = out_dir / fname

        chunk_size = 1024 * 1024
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
        return out_path


def extract_zip(zip_path: Path, out_dir: Path) -> list[Path]:
    extracted = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            target = out_dir / member
            if member.endswith("/"):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(target, "wb") as dst:
                dst.write(src.read())
            extracted.append(target)
    return extracted


def preview_csvs(paths: list[Path], max_rows: int = 3):
    if pd is None:
        print("Note: pandas not installed — skipping CSV preview.")
        return
    for p in paths:
        if p.suffix.lower() != ".csv":
            continue
        try:
            df = pd.read_csv(p, nrows=0)
            cols = list(df.columns)
            total_rows = sum(1 for _ in open(p, "rb")) - 1
            print(f"[CSV] {p.name}: {total_rows} rows, {len(cols)} columns")
            df_head = pd.read_csv(p, nrows=max_rows)
            print(df_head.head(max_rows).to_string(index=False))
        except Exception as e:
            print(f"[WARN] Could not read {p.name}: {e}")


def main():
    ap = argparse.ArgumentParser(description="Download Carbon Monitor data from the API endpoint.")
    ap.add_argument("--url", default=ENDPOINT, help="Download URL (default: official endpoint)")
    ap.add_argument("--out", default="dataset_emission", help="Target directory (default: ./dataset_emission)")
    ap.add_argument("--preview", action="store_true", help="Show a brief CSV preview (requires pandas)")
    args = ap.parse_args()

    out_dir = Path(args.out)
    print(f"Downloading: {args.url}")
    try:
        file_path = download(args.url, out_dir)
    except requests.HTTPError as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Saved to: {file_path}")

    csv_paths = []
    if file_path.suffix.lower() == ".zip":
        print("ZIP detected — extracting…")
        extracted = extract_zip(file_path, file_path.parent)
        print(f"Extracted: {len(extracted)} file(s).")
        csv_paths = [p for p in extracted if p.suffix.lower() == ".csv"]
        if not csv_paths:
            print("Note: No CSVs found in ZIP (or different structure).")
    elif file_path.suffix.lower() == ".csv":
        csv_paths = [file_path]
    else:
        print("Unknown format — please inspect the downloaded file.")

    if args.preview and csv_paths:
        preview_csvs(csv_paths)

    print("Done.")


if __name__ == "__main__":
    main()
