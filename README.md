# Japan labour-market data

This repo holds the Japan data for the regional-studies group project *Fewer Workers, Different Problems: Demographic Decline in Japan, South Korea and China*. Each script downloads public statistics from one source, tidies them into a common CSV format, and the chart script draws the charts for the group's choice of focus sectors and period.

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/fetch_un_wpp.py
.venv/bin/python scripts/fetch_worldbank.py
.venv/bin/python scripts/fetch_boj_tankan.py
.venv/bin/python scripts/fetch_esri.py
.venv/bin/python scripts/fetch_estat_hellowork.py   # needs an e-Stat app ID, see below
.venv/bin/python scripts/make_charts.py
```

`fetch_estat_hellowork.py` needs a free e-Stat app ID. Register at [e-stat.go.jp](https://www.e-stat.go.jp/api/), then put the ID in a `.env` file in the repo root (it's gitignored):

```
ESTAT_APP_ID=your-app-id
```

The scripts reuse files already in `data/raw/`, so reruns are quick. Delete a file there to download it again.

## What's in it

| Script | Source | Output in `data/processed/` | Covers |
|---|---|---|---|
| `fetch_un_wpp.py` | UN World Population Prospects 2024 | `un_wpp_japan_population.csv` | Total and working-age (15–64) population, 1950–2100 |
| `fetch_worldbank.py` | World Bank WDI | `worldbank_japan.csv` | GDP per capita and per worker (PPP), unemployment, fertility, employment shares, 1960–2025 |
| `fetch_boj_tankan.py` | Bank of Japan Tankan | `boj_tankan_employment_di.csv` | Staff-shortage index (employment conditions DI) by industry, quarterly, 1974–2026 |
| `fetch_esri.py` | Cabinet Office ESRI national accounts (2020 base) | `esri_by_industry.csv` | Real value added, persons employed, employees and hours worked by industry, 1994–2024 |
| `fetch_estat_hellowork.py` | MHLW Hello Work statistics, via e-Stat | `estat_hellowork_by_occupation.csv` | Job openings and openings per applicant by occupation, 2013–2025 |
| `make_charts.py` | the files above | `charts/*.png` | Six charts on population, shortages, employment and productivity |

Every CSV has the same columns, so the files can be stacked and the Korea and China data can follow the same format:

| Column | Meaning |
|---|---|
| `source` | Publisher and table |
| `indicator` | What is measured |
| `sector`, `sector_en` | Industry or occupation in Japanese and English. Below the top level it's a `parent/child` path |
| `level` | 0 = total, 1 = top-level sector, 2+ = sub-sector |
| `period` | Year, or `YYYYQn` for quarterly data |
| `value`, `unit` | The number and its unit |

## Things to know before using the data

- **Hello Work** counts only jobs listed at public employment offices, so compare trends, not levels. Its occupation classification changed between 2022 and 2023.
- **National accounts** moved to a 2020 base in December 2025, which changed the levels. Don't mix these figures with ones downloaded before then.
- **The Tankan** has no health & social work industry. Use the Hello Work care figures for that sector.
- Working age is 15–64 and all annual data are calendar years, to match the Korea and China data.

[`data-sources.md`](data-sources.md) has the full source list, e-Stat survey codes, access rules and series breaks.

## Citing the data

- e-Stat (Hello Work): 出典：政府統計の総合窓口(e-Stat)（https://www.e-stat.go.jp/）. Say that figures were processed where you calculated ratios or growth rates.
- Bank of Japan, Tankan.
- Cabinet Office, Economic and Social Research Institute, Annual Report on National Accounts.
- United Nations, World Population Prospects 2024.
- World Bank, World Development Indicators.
