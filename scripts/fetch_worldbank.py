"""World Bank WDI series for Japan (no key needed)."""
import json

import pandas as pd

from common import RAW, get, save_tidy

API = "https://api.worldbank.org/v2/country/JPN/indicator/{code}"
YEARS = "1960:2025"

# code: (indicator, unit)
INDICATORS = {
    "SP.POP.TOTL": ("Total population", "persons"),
    "SP.POP.1564.TO": ("Working-age population (15-64)", "persons"),
    "SP.POP.1564.TO.ZS": ("Working-age population share", "% of total population"),
    "SP.DYN.TFRT.IN": ("Total fertility rate", "births per woman"),
    "SL.UEM.TOTL.ZS": ("Unemployment rate (modelled ILO estimate)", "% of labour force"),
    "SL.UEM.TOTL.NE.ZS": ("Unemployment rate (national estimate)", "% of labour force"),
    "SL.AGR.EMPL.ZS": ("Employment share: agriculture", "% of total employment"),
    "SL.IND.EMPL.ZS": ("Employment share: industry", "% of total employment"),
    "SL.SRV.EMPL.ZS": ("Employment share: services", "% of total employment"),
    "NY.GDP.MKTP.PP.KD": ("GDP, PPP", "constant 2021 international $"),
    "NY.GDP.PCAP.PP.KD": ("GDP per capita, PPP", "constant 2021 international $"),
    "SL.GDP.PCAP.EM.KD": ("GDP per person employed, PPP", "constant 2021 international $"),
    "NV.AGR.TOTL.KD.ZG": ("Real value added growth: agriculture", "annual %"),
    "NV.IND.TOTL.KD.ZG": ("Real value added growth: industry (incl. construction)", "annual %"),
    "NV.IND.MANF.KD.ZG": ("Real value added growth: manufacturing", "annual %"),
    "NV.SRV.TOTL.KD.ZG": ("Real value added growth: services", "annual %"),
}


def fetch(code: str) -> list[dict]:
    """Return the series, reusing data/raw/worldbank/<code>.json if saved. Delete that folder to refresh."""
    out = RAW / "worldbank" / f"{code}.json"
    if out.exists():
        payload = json.loads(out.read_text())
    else:
        payload = get(API.format(code=code), params={"format": "json", "date": YEARS, "per_page": 500}).json()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    if len(payload) < 2 or payload[1] is None:
        raise RuntimeError(f"World Bank returned no data for {code}: {payload[0]}")
    return [r for r in payload[1] if r["value"] is not None]


def main() -> None:
    rows = []
    for code, (indicator, unit) in INDICATORS.items():
        records = fetch(code)
        rows += [{"indicator": indicator, "unit": unit, "period": int(r["date"]), "value": r["value"]} for r in records]
        print(f"{code}: {len(records)} years")
    df = pd.DataFrame(rows)

    # GDP per working-age person has no published series, so derive it.
    wide = df.pivot(index="period", columns="indicator", values="value")
    derived = (wide["GDP, PPP"] / wide["Working-age population (15-64)"]).dropna()
    df = pd.concat([df, pd.DataFrame({
        "indicator": "GDP per working-age person, PPP (derived)",
        "unit": "constant 2021 international $",
        "period": derived.index,
        "value": derived.values,
    })])

    df["source"] = "World Bank WDI"
    df["sector"], df["sector_en"], df["level"] = "合計", "Total", 0
    save_tidy(df.sort_values(["indicator", "period"]), "worldbank_japan")


if __name__ == "__main__":
    main()
