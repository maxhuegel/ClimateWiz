from pathlib import Path
import pandas as pd

BASE    = Path(__file__).resolve().parent
IN_DIR  = BASE / "temp_per_country"
OUT_PER = IN_DIR / "yearly_temp_per_country"
OUT_AGG = IN_DIR / "yearly_temp_aggregated"
OUT_PER.mkdir(parents=True, exist_ok=True)
OUT_AGG.mkdir(parents=True, exist_ok=True)

MASTER = OUT_AGG / "country_year.csv"
MIN_MONTHS = 10

def list_monthly_csvs() -> list[Path]:
    return sorted([p for p in IN_DIR.glob("*.csv") if p.is_file()])

def load_monthly_csv(p: Path) -> pd.DataFrame:
    df = pd.read_csv(p)
    if "country" not in df.columns:
        df["country"] = p.stem.replace("_", " ").strip()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["year"]  = df["date"].dt.year
        df["month"] = df["date"].dt.month
    else:
        if not {"year","month"}.issubset(df.columns):
            raise ValueError(f"{p.name}: missing 'date' or ('year','month')")
        df["year"]  = pd.to_numeric(df["year"], errors="coerce")
        df["month"] = pd.to_numeric(df["month"], errors="coerce")

    if "temp_c" not in df.columns:
        raise ValueError(f"{p.name}: missing 'temp_c'")

    df = df[["country","year","month","temp_c"]].dropna(subset=["year","month","temp_c"])
    df["year"]  = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    return df

def main():
    files = list_monthly_csvs()
    if not files:
        raise FileNotFoundError(f"No csv in {IN_DIR} found.")

    parts, skipped = [], 0
    for p in files:
        try:
            mdf = load_monthly_csv(p)
            g = (mdf.groupby(["country","year"], as_index=False)
                    .agg(n_months=("temp_c","count"),
                         temp_c=("temp_c","mean")))
            g = g[g["n_months"] >= MIN_MONTHS].drop(columns="n_months")
            if g.empty:
                skipped += 1
                continue
            parts.append(g)
        except Exception as e:
            skipped += 1
            print(f"[WARN] skip {p.name}: {e}")

    if not parts:
        raise ValueError(f"No yearly data created: (skipped={skipped}).")

    all_years = pd.concat(parts, ignore_index=True)

    base = (all_years.query("1991<=year<=2024")
                    .groupby("country", as_index=False)["temp_c"].mean()
                    .rename(columns={"temp_c":"base"}))
    all_years = all_years.merge(base, on="country", how="left")
    all_years["anom"] = all_years["temp_c"] - all_years["base"]

    all_years.sort_values(["country","year"]).to_csv(MASTER, index=False)

    for country, sub in all_years.groupby("country", sort=True):
        fn = OUT_PER / f"{country.replace(' ','_')}.csv"
        sub[["country","year","temp_c","base","anom"]].to_csv(fn, index=False)

    print(f"[OK] Master: {MASTER}")
    print(f"[OK] Per-country files: {len(list(OUT_PER.glob('*.csv')))} | skipped={skipped}")

if __name__ == "__main__":
    main()
