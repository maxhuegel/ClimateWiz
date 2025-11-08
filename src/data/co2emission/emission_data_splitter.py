#!/usr/bin/env python3
import argparse
import re
from pathlib import Path
import zipfile
import pandas as pd
import csv

def safe_name(name: str) -> str:
    s = (name or "").strip()
    s = re.sub(r"[^\w\-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "unknown"

def write_chunk(groups, out_dir: Path, header_written: set[str]):
    for country, g in groups:
        sub = g.loc[:, ["country", "date", "value"]]
        fname = f"{safe_name(country)}.csv"
        out_path = out_dir / fname
        write_header = fname not in header_written and not out_path.exists()
        sub.to_csv(out_path, mode="a", index=False, header=write_header)
        if write_header:
            header_written.add(fname)

def sort_country_files(out_dir: Path):
    for p in out_dir.glob("*.csv"):
        try:
            df = pd.read_csv(p, dtype={"country": "string", "date": "string"}, low_memory=False)
            df = df.sort_values("date")
            df.to_csv(p, index=False)
        except Exception:
            pass

COMMON_DELIMS = [",", ";", "\t", "|", ":"]

def sniff_delimiter_from_bytes(sample: bytes) -> str | None:
    try:
        text = sample.decode("utf-8", errors="ignore")
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(text, delimiters="".join(COMMON_DELIMS))
        return dialect.delimiter
    except Exception:
        counts = {d: text.count(d) for d in COMMON_DELIMS}
        best = max(counts, key=counts.get)
        return best if counts.get(best, 0) > 0 else None

def detect_sep_file(path: Path, sample_bytes: int = 200_000) -> str | None:
    try:
        with open(path, "rb") as f:
            return sniff_delimiter_from_bytes(f.read(sample_bytes))
    except Exception:
        return None

def detect_sep_zip_member(zip_path: Path, member: str, sample_bytes: int = 200_000) -> str | None:
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            with zf.open(member) as f:
                return sniff_delimiter_from_bytes(f.read(sample_bytes))
    except Exception:
        return None

def iter_input_csvs(src: Path):
    if src.is_dir():
        any_csv = False
        for p in src.glob("*.csv"):
            any_csv = True
            yield ("file", p)
        if not any_csv:
            raise FileNotFoundError(f"No *.csv found in directory: {src}")
    elif src.is_file():
        if src.suffix.lower() == ".csv":
            yield ("file", src)
        elif src.suffix.lower() == ".zip":
            with zipfile.ZipFile(src, "r") as zf:
                names = [n for n in zf.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
                if not names:
                    raise FileNotFoundError(f"No CSV members found in ZIP: {src}")
                for name in names:
                    yield ("zip", (src, name))
        else:
            raise ValueError(f"Unsupported file type: {src.suffix}")
    else:
        raise FileNotFoundError(f"Path not found: {src}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="dataset_emission")
    ap.add_argument("--out", default="emission_per_country")
    ap.add_argument("--chunksize", type=int, default=200_000)
    ap.add_argument("--sort", action="store_true")
    ap.add_argument("--sep", default=None)
    args = ap.parse_args()

    src = Path(args.input)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    header_written: set[str] = set()
    any_processed = False

    for kind, handle in iter_input_csvs(src):
        if kind == "file":
            csv_path = handle
            sep = args.sep or detect_sep_file(csv_path) or ","
            reader = pd.read_csv(
                csv_path,
                chunksize=args.chunksize,
                sep=sep,
                engine="c",
                usecols=lambda c: str(c).lower() in {"country", "date", "value", "sector"},
                dtype={"country": "string", "date": "string"},
                low_memory=True,
                on_bad_lines="skip",
            )
            for chunk in reader:
                chunk.columns = [str(c).lower() for c in chunk.columns]
                chunk = chunk.loc[:, ["country", "date", "value"]].dropna(subset=["country", "date", "value"])
                write_chunk(chunk.groupby("country", sort=False), out_dir, header_written)
                any_processed = True

        elif kind == "zip":
            zip_path, member_name = handle
            sep = args.sep or detect_sep_zip_member(zip_path, member_name) or ","
            with zipfile.ZipFile(zip_path, "r") as zf, zf.open(member_name) as f:
                reader = pd.read_csv(
                    f,
                    chunksize=args.chunksize,
                    sep=sep,
                    engine="c",
                    usecols=lambda c: str(c).lower() in {"country", "date", "value", "sector"},
                    dtype={"country": "string", "date": "string"},
                    low_memory=True,
                    on_bad_lines="skip",
                )
                for chunk in reader:
                    chunk.columns = [str(c).lower() for c in chunk.columns]
                    chunk = chunk.loc[:, ["country", "date", "value"]].dropna(subset=["country", "date", "value"])
                    write_chunk(chunk.groupby("country", sort=False), out_dir, header_written)
                    any_processed = True

    if not any_processed:
        raise RuntimeError("No CSV data found in the provided input.")

    if args.sort:
        sort_country_files(out_dir)

if __name__ == "__main__":
    main()
