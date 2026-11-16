"""UN World Population Prospects 2024: Japan's population by age, 1950-2100 (CSV, no token needed)."""
import pandas as pd

from common import RAW, download, save_tidy

URL = ("https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/CSV_FILES/"
       "WPP2024_PopulationByAge5GroupSex_Medium.csv.gz")
JAPAN = 392
LAST_ESTIMATE_YEAR = 2023  # later years are the medium-variant projection


def main() -> None:
    path = download(URL, RAW / "un" / "WPP2024_PopulationByAge5GroupSex_Medium.csv.gz")
    columns = ["LocID", "Variant", "Time", "AgeGrpStart", "PopTotal"]
    japan = pd.concat(chunk[chunk.LocID == JAPAN] for chunk in pd.read_csv(path, usecols=columns, chunksize=500_000))
    print(f"Japan rows: {len(japan):,}, variants {japan.Variant.unique().tolist()}, years {japan.Time.min()}-{japan.Time.max()}")

    total = japan.groupby("Time").PopTotal.sum()
    working = japan[japan.AgeGrpStart.between(15, 60)].groupby("Time").PopTotal.sum()
    series = {
        ("Total population", "thousand persons"): total,
        ("Working-age population (15-64)", "thousand persons"): working,
        ("Working-age population share", "% of total population"): working / total * 100,
    }
    df = pd.concat(
        pd.DataFrame({"indicator": indicator, "unit": unit, "period": s.index, "value": s.values})
        for (indicator, unit), s in series.items()
    )
    df["source"] = df.period.map(lambda y: "UN WPP 2024 estimate" if y <= LAST_ESTIMATE_YEAR else "UN WPP 2024 medium projection")
    df["sector"], df["sector_en"], df["level"] = "合計", "Total", 0
    save_tidy(df, "un_wpp_japan_population")


if __name__ == "__main__":
    main()
