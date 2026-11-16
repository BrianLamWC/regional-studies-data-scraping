# Japan data sources and access requirements

Checked on 2026-11-07. ✅ = confirmed against the official page, code or API. ⚠️ = not confirmed this session.

## Recommendation: extract broadly now, choose sector and period later

Extracting more sectors or years costs almost nothing, and these tables are small. What constrains the choice is **series breaks**, not volume. So:

1. **Pull every industry at the broadest level** (大分類, the major industry divisions, about 20 industries). The Statistics Bureau says this level connects across the 2024 industry-classification revision with little disruption ✅. Narrow down later.
2. **Pull each series back as far as it stays consistent**, then trim to the agreed window.
3. **Proposed window for the Nov 13 meeting:** 1995 to latest, annual. Japan's working-age population (15–64) **peaked in 1995** at 87.5m and has since fallen 17.1% to 72.5m (2025) ✅ (World Bank). If the group wants one window for all three countries, 1990 to latest covers Korea's peak (2018) and China's (2015) as well. Use annual frequency as the common base, because GDP by industry is annual only.
4. **Choosing focus sectors (proposal):** pick 3–4 where shortage data and Japan's policy response overlap: **construction, medical and welfare (care), transport and logistics, accommodation and food service, manufacturing**. Two reasons:
   - These show up in labour-shortage measures and among the fields of the Specified Skilled Worker (特定技能) visa.
   - They match standard international (ISIC) industry sections, so the Korea and China teams can line up with them.

   Confirm the choice with the shortage indicators below (the Bank of Japan Tankan and 労働経済動向調査) before locking it in.

## Access requirements

| Source | Account or key? | Format | Other limits |
|---|---|---|---|
| **e-Stat** website (most MIC and MHLW surveys) | None to browse and download ✅ | CSV / Excel per table | Mostly Japanese |
| **e-Stat API** | **Yes: free e-Stat user account, then an appId per application** ✅. An unpublished app can use the URL `http://test.localhost/` ✅ | JSON / XML / CSV | 100,000 records per request by default; page with `NEXT_KEY` → `startPosition` ✅. `lang=E` returns English labels ✅. Credit required if you publish an app ✅ |
| **Cabinet Office ESRI** national accounts | None | **Excel only** ✅ | Annual only. Revised to a 2020 base in Dec 2025 ✅ (see pitfalls) |
| **Bank of Japan** time-series site (Tankan) | No key mentioned in the BOJ's API usage notes ✅ | API (since 18 Feb 2026 ✅) or download | No high-frequency access ✅. If you *publish* a service using the API, show the BOJ's credit line and notify post.rsd17@boj.or.jp ✅ |
| **MHLW** website | None | Excel / PDF | Japanese only |
| **World Bank WDI** (Japan, international definitions) | None ✅ | JSON API | Japan's sector series ends at 2024 ✅ |
| **UN World Population Prospects** | CSV: none ✅. API: **free token requested by email**; data endpoints return HTTP 401 without it ✅ | CSV / API | The CSVs are enough, so you can skip the token |
| Individual-level survey microdata | **Formal application** under the Statistics Act (academic purpose, institutional affiliation) | — | Takes weeks. **Not needed** for this project's aggregate tables |

**Citation (e-Stat and other government data):** the terms follow the government standard terms of use v2.0 and are CC BY 4.0-compatible ✅. Cite as `出典：政府統計の総合窓口(e-Stat)（https://www.e-stat.go.jp/）`, and say when you've edited or processed the figures ✅.

**The only blocker before scripting:** register an e-Stat account and create an appId. It's free and self-service.

## Sources by indicator

| Indicator | Source (e-Stat 政府統計コード) | Frequency | Notes |
|---|---|---|---|
| Working-age population | 人口推計 Population Estimates (`00200524`) ✅ | monthly / annual (Oct 1) | 国勢調査 Census (`00200521`) ✅ for 5-yearly benchmarks |
| Births and deaths | 人口動態調査 Vital Statistics (`00450011`) ✅ | monthly / annual | |
| Unemployment | 労働力調査 Labour Force Survey (`00200531`) ✅ | monthly | |
| Employment by sector | 労働力調査 (`00200531`) ✅; 就業構造基本調査 Employment Status Survey (`00200532`) ✅ | monthly; every 5 years | Labour Force Survey switched to the 2024 classification from January 2026 data ✅ |
| Job openings by sector | 一般職業紹介状況 Employment Referrals (`00450222`) ✅ | monthly | **Not in the e-Stat database**: Excel files only, found through the `getDataCatalog` API ✅. The occupation tables (long-run table 21) give openings and openings-per-applicant from 2013. The occupation classification changed between 2022 and 2023 ✅. Industry tables (long-run table 20) start April 2024 on the new industry classification. **Hello Work (public employment office) listings only** |
| Unfilled vacancies by sector | 雇用動向調査 Employment Trend Survey (`00450073`) ✅ | semi-annual | 未充足求人数 tables ✅ |
| Labour shortage by sector | 労働経済動向調査 (`00450072`) ✅; **BOJ Tankan 雇用人員判断DI** (employment conditions DI) by industry ✅ | quarterly | Tankan: share of firms reporting "excessive" staff minus share reporting "insufficient" ✅ |
| Economic growth by sector | 国民経済計算 National Accounts, ESRI (`00100409`) ✅: 経済活動別国内総生産, real / nominal / deflator ✅ | annual (calendar year) | Excel from esri.cao.go.jp ✅. Start year is in the files ⚠️ |
| GDP per working-age person | Compute: real GDP ÷ population aged 15–64 | annual | For cross-country comparison, use World Bank `NY.GDP.MKTP.PP.KD / SP.POP.1564.TO` ✅: Japan 2025 = **82,160** (constant 2021 PPP $) |
| Foreign residents by status (incl. 特定技能) | 在留外国人統計 (`00250012`) ✅ | semi-annual | Measures the immigration policy response |
| Foreign workers by industry | MHLW 外国人雇用状況 届出状況 (employer reports on foreign workers) ⚠️ | annual (end of October) | |
| Specified Skilled Worker residents by field | Immigration Services Agency (moj.go.jp/isa) ⚠️ | semi-annual (per press coverage) | The official page didn't load for automated fetching |
| Population projections | IPSS 将来推計人口 ⚠️ | ~5-yearly | |

### Policy documents (the deck calls the data work "mostly policy")

All are free public web pages or PDFs, mostly in Japanese. None were checked individually this session ⚠️.
- **Fertility and children:** Children and Families Agency (こども家庭庁): こども未来戦略 (2023), こども白書 (annual)
- **Labour:** MHLW 労働経済白書 (White Paper on the Labour Economy, annual, with English summary)
- **Immigration:** Immigration Services Agency: the Specified Skilled Worker (特定技能) system, intake caps by field, and the 育成就労 system replacing the Technical Intern Training programme
- **Legislation:** e-Gov 法令検索 (e.g. 高年齢者雇用安定法, the act on employment of older workers)

## Pitfalls (Japan)

- **Industry classification revision (14th):** in force from April 2024 ✅. Each survey switches at its own time: the Labour Force Survey from January 2026 data ✅, and the Monthly Labour Survey had not switched yet when MHLW wrote its plan ✅. Stay at the 大分類 level to bridge the break.
- **National accounts 2020-base revision (Dec 2025)** ✅: levels changed (2020 nominal GDP ¥539.6tn → ¥554.1tn). Download every year from the **same vintage** and never mix with figures saved before Dec 2025.
- **Fiscal vs calendar year:** ESRI publishes both 年度 (Apr–Mar) and 暦年. Use 暦年 (calendar year) to match the World Bank and the other countries.
- **Hello Work coverage:** excludes private job sites. Compare trends, not levels.

## Sources

- e-Stat survey pages: `https://www.e-stat.go.jp/statistics/<code>`; API guide: <https://www.e-stat.go.jp/api/api-info/api-guide>; API spec: <https://www.e-stat.go.jp/api/api-info/e-stat-manual3-0>; terms: <https://www.e-stat.go.jp/terms-of-use>
- ESRI 2024 annual national accounts (2020 base): <https://www.esri.cao.go.jp/jp/sna/data/data_list/kakuhou/files/2024/2024_kaku_top.html>; 2020-base revision: <https://www.esri.cao.go.jp/jp/sna/seibi/kouhou/2020kijun.html>
- BOJ API notice: <https://www.boj.or.jp/statistics/outline/notice_2026/not260218a.htm>; usage notes: <https://www.stat-search.boj.or.jp/info/api_notice.pdf>
- Industry classification revision: <https://www.soumu.go.jp/menu_news/s-news/01toukatsu01_02000212.html>; Labour Force Survey switch: <https://www.stat.go.jp/data/roudou/pdf/260130.pdf>; Monthly Labour Survey plan: <https://www.mhlw.go.jp/content/10700000/001729990.pdf>
- World Bank API: <https://api.worldbank.org/v2/>; UN WPP Data Portal API: <https://population.un.org/dataportalapi/api/v1/>
- Specified Skilled Worker totals (press): <https://www.nippon.com/ja/japan-data/h02750/>
