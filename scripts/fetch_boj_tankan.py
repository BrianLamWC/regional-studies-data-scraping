"""Bank of Japan Tankan: employment conditions DI by industry (no key needed).

DI = % of firms answering "excessive" minus % answering "insufficient", so negative means a shortage.
API manual: https://www.stat-search.boj.or.jp/info/api_manual.pdf
Usage notes (no high-frequency access): https://www.stat-search.boj.or.jp/info/api_notice.pdf
"""
import json
import re
import time

import pandas as pd

from common import RAW, get, save_tidy

API = "https://www.stat-search.boj.or.jp/api/v1/"
# Employment conditions DI, all firm sizes, actual result (not the forecast). The first digit after
# TK99F is the industry group: 0 all industries, 1 and 3 manufacturing, 2 nonmanufacturing,
# 5 financial institutions (surveyed separately, from 2004).
CODE = re.compile(r"^TK99F(\d)\d{3}608GCQ00000$")
PARENT = {"1": ("製造業", "Manufacturing"), "3": ("製造業", "Manufacturing"),
          "2": ("非製造業", "Nonmanufacturing"), "5": ("金融機関", "Financial institutions")}
MAX_CODES_PER_REQUEST = 250


def industry(name: str) -> str:
    # Names end ".../<industry>/実績" (actual result). Most also carry a firm-size part before the
    # industry, but the financial-institution series do not, so count from the end.
    return name.split("/")[-2]


def classify(series: dict) -> tuple[str, str, int]:
    jp, en = industry(series["NAME_OF_TIME_SERIES_J"]), industry(series["NAME_OF_TIME_SERIES"])
    depth = len(jp) - len(jp.lstrip("_"))
    jp, en = jp.lstrip("_"), en.lstrip("_")
    group = CODE.match(series["SERIES_CODE"]).group(1)
    if group == "0":
        return jp, en, 0
    if depth == 0:
        return jp, en, 1
    parent_jp, parent_en = PARENT[group]
    return f"{parent_jp}/{jp}", f"{parent_en}/{en}", depth + 1


def main() -> None:
    meta = get(API + "getMetadata", params={"format": "json", "lang": "jp", "db": "CO"}).json()
    (RAW / "boj").mkdir(parents=True, exist_ok=True)
    (RAW / "boj" / "co_metadata.json").write_text(json.dumps(meta, ensure_ascii=False))

    series = [s for s in meta["RESULTSET"] if CODE.match(s.get("SERIES_CODE") or "")]
    latest = max(s["END_OF_THE_TIME_SERIES"] for s in series)
    series = [s for s in series if s["END_OF_THE_TIME_SERIES"] == latest]  # drop discontinued industries
    names = {s["SERIES_CODE"]: classify(s) for s in series}
    print(f"{len(names)} current industry series, latest quarter {latest}")

    rows, codes = [], list(names)
    for i in range(0, len(codes), MAX_CODES_PER_REQUEST):
        chunk, start = codes[i:i + MAX_CODES_PER_REQUEST], None
        while True:
            params = {"format": "json", "lang": "jp", "db": "CO", "code": ",".join(chunk)}
            if start:
                params["startPosition"] = start
            data = get(API + "getDataCode", params=params).json()
            if data.get("STATUS") != 200:
                raise RuntimeError(f"BOJ API error {data.get('STATUS')}: {data.get('MESSAGE')}")
            for s in data["RESULTSET"]:
                sector, sector_en, level = names[s["SERIES_CODE"]]
                values = s["VALUES"]
                for date, value in zip(values["SURVEY_DATES"], values["VALUES"]):
                    if value is None:
                        continue
                    date = str(date)
                    rows.append({"sector": sector, "sector_en": sector_en, "level": level,
                                 "period": f"{date[:4]}Q{int(date[4:])}", "value": float(value)})
            start = data.get("NEXTPOSITION")
            time.sleep(1)  # the BOJ asks API users to avoid high-frequency access
            if not start:
                break

    df = pd.DataFrame(rows)
    df["source"] = "Bank of Japan Tankan"
    df["indicator"] = "Employment conditions DI (all firm sizes, actual)"
    df["unit"] = "% points (excessive minus insufficient)"
    save_tidy(df, "boj_tankan_employment_di")


if __name__ == "__main__":
    main()
