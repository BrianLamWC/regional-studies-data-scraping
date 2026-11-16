"""Cabinet Office (ESRI) national accounts: real value added and employment by industry (no key needed).

Files come from the 2024 annual estimates on the 2020 base (published Dec 2025). Never mix them with
figures saved before the Dec 2025 rebase. Calendar-year sheets only, to match other countries.
"""
import re
import unicodedata

import pandas as pd

from common import RAW, download, save_tidy

BASE = "https://www.esri.cao.go.jp/jp/sna/data/data_list/kakuhou/files/2024/tables/"
SOURCE = "Cabinet Office ESRI national accounts (2024 annual estimates, 2020 base)"

# (file, sheet, indicator)
TABLES = [
    ("2024fcm3rn_jp.xlsx", "実数", "Real value added (chain-linked, 2020 prices)"),
    ("2024s3_jp.xlsx", "暦年（１）就業者", "Persons employed"),
    ("2024s3_jp.xlsx", "暦年（２）雇用者", "Employees"),
    ("2024s3_jp.xlsx", "暦年（３）労働時間数", "Hours worked"),
]

# Top-level industries with their ISIC Rev.4 sections, so the Korea and China teams can match them.
INDUSTRY_EN = {
    "農林水産業": "Agriculture, forestry & fishing (A)",
    "鉱業": "Mining (B)",
    "製造業": "Manufacturing (C)",
    "電気・ガス・水道・廃棄物処理業": "Electricity, gas, water & waste (D+E)",
    "建設業": "Construction (F)",
    "卸売・小売業": "Wholesale & retail (G)",
    "運輸・郵便業": "Transport & postal (H)",
    "宿泊・飲食サービス業": "Accommodation & food service (I)",
    "情報通信業": "Information & communication (J)",
    "金融・保険業": "Finance & insurance (K)",
    "不動産業": "Real estate (L)",
    "専門・科学技術、業務支援サービス業": "Professional, scientific & support services (M+N)",
    "公務": "Public administration (O)",
    "教育": "Education (P)",
    "保健衛生・社会事業": "Health & social work (Q)",
    "その他のサービス": "Other services (R+S+T)",
}
TOTAL_EN = {"国内総生産": "GDP", "合計": "Total", "小計": "Subtotal (industries)"}


def clean(text) -> str:
    """NFKC-normalise (full-width digits and brackets to ASCII) and drop all whitespace."""
    return re.sub(r"\s", "", unicodedata.normalize("NFKC", str(text)))


INDUSTRY_EN = {clean(k): v for k, v in INDUSTRY_EN.items()}


def is_year(value) -> bool:
    return isinstance(value, (int, float)) and not pd.isna(value) and float(value).is_integer() and 1990 <= value <= 2100


def parse(path, sheet: str, indicator: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet, header=None)
    year_row = next(i for i, row in df.iterrows() if sum(is_year(v) for v in row.iloc[1:]) >= 5)
    years = {col: int(v) for col, v in df.iloc[year_row].items() if col != 0 and is_year(v)}
    header = clean(" ".join(str(v) for v in df.iloc[:year_row].stack()))
    unit_match = re.search(r"単位:([^)]+)\)", header)
    unit = unit_match.group(1) if unit_match else ""

    rows, parent, seen = [], None, set()
    for _, row in df.iloc[year_row + 1:].iterrows():
        if pd.isna(row.iloc[0]):
            continue
        name = clean(row.iloc[0])
        if top := re.match(r"^\d+\.(.+)$", name):
            level, sector = 1, top.group(1)
            parent, sector_en = sector, INDUSTRY_EN.get(sector, "")
        elif sub := re.match(r"^\(\d+\)(.+)$", name):
            level, sector, sector_en = 2, f"{parent}/{sub.group(1)}", ""
        else:
            level, sector, sector_en = 0, name, TOTAL_EN.get(name, "")
        if sector in seen:  # the employment sheets repeat the total
            continue
        seen.add(sector)
        for col, year in years.items():
            value = pd.to_numeric(row[col], errors="coerce")
            if pd.notna(value):
                rows.append({"sector": sector, "sector_en": sector_en, "level": level, "period": year, "value": float(value)})

    out = pd.DataFrame(rows)
    out["indicator"], out["unit"], out["source"] = indicator, unit, SOURCE
    missing = sorted(set(INDUSTRY_EN) - set(out.loc[out.level == 1, "sector"]))
    if missing:
        raise RuntimeError(f"{path.name} [{sheet}]: top-level industries not found: {missing}")
    print(f"{path.name} [{sheet}]: {out.sector.nunique()} rows, {min(years.values())}-{max(years.values())}, unit {unit!r}")
    return out


def main() -> None:
    frames = []
    for file, sheet, indicator in TABLES:
        path = download(BASE + file, RAW / "esri" / file)
        frames.append(parse(path, sheet, indicator))
    save_tidy(pd.concat(frames), "esri_by_industry")


if __name__ == "__main__":
    main()
