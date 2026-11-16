# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Run everything from the repo root. There are no tests or linter.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # one-time setup
.venv/bin/python scripts/fetch_worldbank.py   # World Bank WDI; API is often slow. Reuses data/raw/worldbank/*.json; delete them to refresh
.venv/bin/python scripts/fetch_boj_tankan.py  # Bank of Japan Tankan employment conditions DI by industry
.venv/bin/python scripts/fetch_esri.py        # Cabinet Office national accounts: real value added, employment, hours by industry
.venv/bin/python scripts/fetch_un_wpp.py      # UN WPP 2024 population by age (30 MB download, cached)
.venv/bin/python scripts/fetch_estat_hellowork.py  # Hello Work openings and openings-per-applicant by occupation (needs .env key)
.venv/bin/python scripts/make_charts.py       # charts/*.png, built only from data/processed/
```

## Architecture

- **One `scripts/fetch_*.py` per source.** Each one downloads into `data/raw/<source>/` and writes a single CSV to `data/processed/`. All CSVs share the long layout defined in `scripts/common.py`: `source, indicator, sector, sector_en, level, period, value, unit`. New sources (e.g. e-Stat) must use the same layout so the files stack.
  - `level`: 0 = total, 1 = top-level sector, 2+ = sub-sector. Below level 1, `sector` is a `parent/child` path.
  - `period`: a year, or `YYYYQn` for quarterly data.
- **Focus sectors** are the `FOCUS_ESRI` / `FOCUS_TANKAN` constants in `make_charts.py`. They are a proposal the group has not confirmed yet.
- **e-Stat:** the app ID goes in `.env` as `ESTAT_APP_ID` (gitignored).
  - Some statistics are not in the e-Stat database. `getStatsList` returns nothing for Hello Work (`00450222`), for example. Those are Excel files: find them with the `getDataCatalog` API (file catalogue), then download them.
  - The current Hello Work file is replaced monthly, so look it up by name and take the highest `statInfId`. Never hardcode its ID.
  - Hello Work's occupation classification changed between 2022 and 2023. The two files share a row order, which the script asserts before joining them.
- **Source quirks handled in code:**
  - The Tankan financial-institution series names lack the firm-size part, so take the industry from the end of the name.
  - ESRI sheets are parsed by locating the year row and NFKC-normalising the labels.
  - The ESRI files are the Dec 2025 rebase vintage. Never mix them with older downloads.
  - The BOJ asks API users to avoid high-frequency access, so the script sleeps between requests.

## Project context

This is the data-collection side of a regional-studies group project, *"Fewer Workers, Different Problems: Demographic Decline in Japan, South Korea and China"* (Economics & Business).

**Research question:** As working-age populations and birth rates fall, how have Japan, South Korea and China been affected, how have they responded, and why do the impacts and responses differ?

The comparison rests on these points: all three countries have among the world's lowest fertility rates, but they are at different stages of ageing and economic development, and each faces a different main constraint (jobs vs. workers). The analysis looks at the number of working-age people, the share of them employed, output per worker, and policy responses.

**Example target variables** (the group compares these across all three countries, so keep definitions, units and time ranges comparable):
- Working-age population
- Annual births and deaths
- Sector-specific job openings
- GDP per capita
- Unemployment rate
- Employment by sector

**Sources named in the deck:**
- UN World Population Prospects
- National statistics offices and labour ministries:
  - Japan: e-Stat, MHLW
  - Korea: KOSIS, Ministry of Employment and Labor
  - China: NBS, MOHRSS
- ILO, World Bank (WBG) and OECD data
- Studies by the IMF, the Bank of Korea and KDI
- Government policy documents

**Scope of this repo: Japan only.** The repo owner (Brian) is responsible for the Japan data. Korea, China, the literature review and the research design belong to other group members. Keep Japan series in definitions the other teams can match (15–64 working age, calendar years, major industry divisions). The deck marks the country data work as "mostly policy," so the job covers Japan's policy responses as well as the numeric series.

**Undecided:** the group has not yet chosen the focus sectors or the time period. Until it does, extract every industry at the 大分類 level and each series back as far as it stays consistent. Trim later.

**`data-sources.md`** lists the Japan sources by indicator, with e-Stat survey codes, the account and API-key requirements, citation rules, and the series breaks (the 2024 industry-classification revision and the Dec 2025 national accounts rebase). Check it before adding a new source, and update it when you verify or replace an entry.
