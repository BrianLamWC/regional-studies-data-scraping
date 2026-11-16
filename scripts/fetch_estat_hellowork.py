"""MHLW Employment Referrals (一般職業紹介状況, Hello Work): job openings and openings-to-applicants ratio by occupation.

These tables are Excel files in the e-Stat file catalogue, not in the e-Stat database, so the script finds the
newest files with the getDataCatalog API (needs ESTAT_APP_ID in .env) and downloads them. There are two
occupation classifications:
  - 2013-2022: 2011 MHLW occupation classification (final file, no longer updated)
  - 2023 on:   Japan Standard Occupational Classification (file replaced every month)
Rows come in the same order in both files, so old rows take the current labels (asserted below), but treat
2022 -> 2023 as a classification break. Annual figures are averages of monthly values, regular jobs including
part-time (パート含む常用). Hello Work listings only: private job sites are not counted.
"""
import re
import unicodedata
from urllib.parse import parse_qs, urlparse

import pandas as pd
from dotenv import dotenv_values

from common import RAW, ROOT, download, get, save_tidy

CATALOG = "https://api.e-stat.go.jp/rest/3.0/app/json/getDataCatalog"
STATS_CODE = "00450222"
# classification label -> start of the resource name in the e-Stat catalogue
FILES = {
    "2011 MHLW occupation classification": "長期時系列表_21_職業別労働市場関係指標（実数）（平成23年改定）",
    "current occupation classification": "長期時系列表_21_職業別労働市場関係指標（実数）（平成21年改定）（令和4年4月～）",
}
# sheet-name fragment -> (indicator, unit)
SHEETS = {
    "有効求人倍率（パート含む常用）": ("Active openings-to-applicants ratio", "openings per applicant (annual average)"),
    "新規求人（パート含む常用）": ("New job openings", "openings per month (annual average)"),
}
MAJOR_EN = {
    "職業計": "All occupations",
    "管理的職業従事者": "Managers",
    "専門的・技術的職業従事者": "Professional & technical",
    "事務従事者": "Clerical",
    "販売従事者": "Sales",
    "サービス職業従事者": "Service",
    "保安職業従事者": "Security",
    "農林漁業従事者": "Agriculture, forestry & fishing",
    "生産工程従事者": "Production process",
    "輸送・機械運転従事者": "Transport & machine operation",
    "建設・採掘従事者": "Construction & mining",
    "運搬・清掃・包装等従事者": "Carrying, cleaning & packaging",
    "分類不能の職業": "Unclassifiable",
    "介護関係職種": "Care-related occupations",  # cross-cutting aggregate defined in the tables' note 2
}
MINOR_EN = {
    "介護サービス職業従事者": "Care service workers",
    "保健師,助産師,看護師": "Nurses & midwives",
    "社会福祉専門職業従事者": "Social welfare professionals",
    "自動車運転従事者": "Motor vehicle drivers",
    "飲食物調理従事者": "Cooks",
    "接客・給仕職業従事者": "Waiting & serving staff",
    "建設躯体工事従事者": "Construction framework workers",
    "土木作業従事者": "Civil engineering workers",
    "建築・土木・測量技術者": "Architects & civil engineers",
}


def clean(text) -> str:
    text = re.sub(r"\s", "", unicodedata.normalize("NFKC", str(text)))
    return re.sub(r"\(注\d+\)$", "", text)


def as_list(x):
    return x if isinstance(x, list) else [x]


def text(x) -> str:
    return x.get("$", "") if isinstance(x, dict) else ("" if x is None else str(x))


def find_files(app_id: str) -> dict[str, str]:
    """Return {classification: download URL}, taking the newest upload when a name matches more than once."""
    data = get(CATALOG, params={"appId": app_id, "statsCode": STATS_CODE, "searchWord": "職業別"}).json()["GET_DATA_CATALOG"]
    if data["RESULT"]["STATUS"] != 0:
        raise RuntimeError(f"e-Stat catalogue error {data['RESULT']['STATUS']}: {data['RESULT']['ERROR_MSG']}")
    found: dict[str, tuple[int, str]] = {}
    for dataset in as_list(data["DATA_CATALOG_LIST_INF"]["DATA_CATALOG_INF"]):
        for resource in as_list(dataset["RESOURCES"]["RESOURCE"]):
            name = text(resource["TITLE"].get("NAME"))
            for label, prefix in FILES.items():
                if name.startswith(prefix):
                    stat_id = int(parse_qs(urlparse(resource["URL"]).query)["statInfId"][0])
                    if stat_id > found.get(label, (0, ""))[0]:
                        found[label] = (stat_id, resource["URL"])
    missing = set(FILES) - set(found)
    if missing:
        raise RuntimeError(f"e-Stat catalogue has no file for: {missing}")
    return {label: url for label, (_, url) in found.items()}


def parse(path) -> dict[str, list[tuple[str, dict[int, float]]]]:
    """Return {indicator: [(occupation label, {year: value}), ...]} in sheet row order."""
    book = pd.ExcelFile(path)
    out = {}
    for fragment, (indicator, _) in SHEETS.items():
        sheet = next(s for s in book.sheet_names if fragment in s)
        df = pd.read_excel(book, sheet_name=sheet, header=None)
        annual = [c for c in df.columns[1:]
                  if isinstance(df.iat[1, c], str) and re.fullmatch(r"\d{4}年", df.iat[1, c].strip()) and pd.isna(df.iat[3, c])]
        rows = []
        for i in range(5, len(df)):
            label = df.iat[i, 0]
            if pd.isna(label) or clean(label).startswith("(注"):
                continue
            values = {int(df.iat[1, c].strip()[:4]): float(df.iat[i, c]) for c in annual if pd.notna(df.iat[i, c])}
            rows.append((clean(label), values))
        out[indicator] = rows
    return out


def main() -> None:
    app_id = dotenv_values(ROOT / ".env").get("ESTAT_APP_ID")
    if not app_id:
        raise SystemExit("Set ESTAT_APP_ID in .env (free app ID from e-stat.go.jp)")
    parsed = {}
    for label, url in find_files(app_id).items():
        stat_id = parse_qs(urlparse(url).query)["statInfId"][0]
        path = download(url, RAW / "estat" / f"hellowork_occupation_{stat_id}.xlsx")
        parsed[label] = parse(path)
        print(f"{label}: {path.name}")

    old, new = parsed["2011 MHLW occupation classification"], parsed["current occupation classification"]
    rows = []
    for indicator, unit in SHEETS.values():
        new_rows, old_rows = new[indicator], old[indicator]
        if len(new_rows) != len(old_rows) or new_rows[0][0] != old_rows[0][0] or not old_rows[-1][0].startswith("介護関係職種"):
            raise RuntimeError(f"{indicator}: the two classifications no longer line up row by row; map them by hand")
        parent = None
        for (label, new_values), (_, old_values) in zip(new_rows, old_rows):
            if label in MAJOR_EN:
                level = 0 if label == "職業計" else 1
                sector, sector_en = label, MAJOR_EN[label]
                if label != "介護関係職種":
                    parent = (label, MAJOR_EN[label])
            else:
                level = 2
                sector, sector_en = f"{parent[0]}/{label}", f"{parent[1]}/{MINOR_EN.get(label, '')}".rstrip("/")
            for classification, values in [("2011 MHLW occupation classification", old_values),
                                           ("current occupation classification", new_values)]:
                for year, value in values.items():
                    rows.append({"source": f"MHLW Employment Referrals (Hello Work), {classification}",
                                 "indicator": indicator, "unit": unit, "sector": sector, "sector_en": sector_en,
                                 "level": level, "period": year, "value": value})
    df = pd.DataFrame(rows)
    dupes = df.duplicated(["indicator", "sector", "period"]).sum()
    if dupes:
        raise RuntimeError(f"{dupes} years appear in both classification files")
    save_tidy(df, "estat_hellowork_by_occupation")


if __name__ == "__main__":
    main()
