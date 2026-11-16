"""Charts for choosing the focus sectors and period (Japan). Reads data/processed, writes charts/*.png."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import CHARTS, PROCESSED

# Reference palette from the dataviz guidelines (light mode).
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, CONTEXT = "#e1e0d9", "#c3c2b7", "#c3c2b7"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # categorical slots 1-4, fixed order
CARE = "#e87ba4"  # categorical slot 5; validated beside slots 1-3, needs direct labels (CVD 6.1 vs aqua)
HIGHLIGHT = SERIES[0]

# Proposed focus sectors (see data-sources.md). The Tankan has no health & social work series.
FOCUS_ESRI = ["建設業", "運輸・郵便業", "宿泊・飲食サービス業", "保健衛生・社会事業", "製造業"]
FOCUS_TANKAN = {  # sector -> short English label, in fixed colour order
    "非製造業/建設": "Construction",
    "非製造業/運輸・郵便": "Transport & postal",
    "非製造業/宿泊・飲食サービス": "Accommodation & food",
    "製造業": "Manufacturing",
}
BASE_YEAR, LAST_YEAR = 1995, 2024

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": 10,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": INK2,
    "axes.edgecolor": AXIS, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "lines.linewidth": 2,
})


def short(label: str) -> str:
    """'Health & social work (Q)' -> 'Health & social work'."""
    return label.rsplit(" (", 1)[0] if label.endswith(")") else label


def finish(fig, title: str, subtitle: str, source: str, name: str) -> None:
    fig.text(0.02, 0.97, title, fontsize=13.5, fontweight="bold", va="top")
    fig.text(0.02, 0.915, subtitle, fontsize=9.5, color=INK2, va="top", linespacing=1.4)
    fig.text(0.02, 0.02, source, fontsize=8, color=MUTED, va="bottom")
    CHARTS.mkdir(exist_ok=True)
    path = CHARTS / f"{name}.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"wrote {path.relative_to(CHARTS.parent)}")


def spread(values: dict, gap: float) -> dict:
    """Nudge end-label positions apart so they do not overlap."""
    placed, last = {}, None
    for key, value in sorted(values.items(), key=lambda kv: kv[1]):
        y = value if last is None or value - last >= gap else last + gap
        placed[key], last = y, y
    return placed


def working_age_population() -> None:
    un = pd.read_csv(PROCESSED / "un_wpp_japan_population.csv")
    s = un[un.indicator == "Working-age population (15-64)"].set_index("period").value / 1000
    s = s.loc[1950:2070]
    est, proj = s.loc[:2023], s.loc[2023:]
    peak_year, peak = int(s.idxmax()), s.max()

    fig = plt.figure(figsize=(10, 5.6))
    ax = fig.add_axes([0.07, 0.12, 0.88, 0.66])
    ax.plot(est.index, est.values, color=HIGHLIGHT)
    ax.plot(proj.index, proj.values, color=HIGHLIGHT, linestyle=(0, (4, 3)))
    for year, value, text, offset in [
        (peak_year, peak, f"{peak_year} peak\n{peak:.1f}m", (0, 12)),
        (2025, s[2025], f"2025\n{s[2025]:.1f}m", (14, 6)),
        (2070, s[2070], f"2070\n{s[2070]:.1f}m", (-6, 12)),
    ]:
        ax.scatter([year], [value], s=36, color=HIGHLIGHT, edgecolor=SURFACE, linewidth=2, zorder=3)
        ax.annotate(text, (year, value), xytext=offset, textcoords="offset points", ha="center",
                    fontsize=9, color=INK2)
    ax.set_ylim(0, 100)
    ax.set_xlim(1950, 2072)
    ax.set_ylabel("Millions")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    decline = (s[2025] / peak - 1) * 100
    finish(fig,
           f"Japan's working-age population peaked in {peak_year} and has fallen {abs(decline):.0f}% since",
           f"Population aged 15–64. Solid line: UN estimates to 2023. Dashed: UN medium-variant projection, "
           f"{s[2070]:.0f}m by 2070.",
           "Source: UN World Population Prospects 2024 (data/processed/un_wpp_japan_population.csv)",
           "1_working_age_population")


def tankan_by_industry() -> None:
    t = pd.read_csv(PROCESSED / "boj_tankan_employment_di.csv")
    quarter = t.period.max()
    latest = t[t.period == quarter]
    keep = latest[(latest.sector.isin(["全産業", "製造業", "金融機関"]))
                  | ((latest.level == 2) & latest.sector.str.startswith("非製造業/"))]
    keep = keep.assign(label=[FOCUS_TANKAN.get(s, en.split("/")[-1]) for s, en in zip(keep.sector, keep.sector_en)])
    keep = keep.sort_values("value", ascending=False)  # most negative ends up on top

    fig = plt.figure(figsize=(10, 6.4))
    ax = fig.add_axes([0.33, 0.15, 0.62, 0.65])
    colors = [MUTED if s == "全産業" else HIGHLIGHT if s in FOCUS_TANKAN else CONTEXT for s in keep.sector]
    ax.barh(keep.label, keep.value, color=colors, height=0.62)
    for y, v in enumerate(keep.value):
        ax.text(v - 1, y, f"{v:.0f}", va="center", ha="right", fontsize=8.5, color=INK2)
    for tick, sector in zip(ax.get_yticklabels(), keep.sector):
        tick.set_fontweight("bold" if sector in FOCUS_TANKAN else "normal")
    ax.axvline(0, color=AXIS, linewidth=1)
    ax.set_xlim(keep.value.min() - 10, 5)
    ax.set_xlabel("DI (% points); further left = more firms short of staff")
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    top = keep.sort_values("value").label.head(3).tolist()
    finish(fig,
           f"Staff shortages are worst in {top[0].lower()}, {top[1].lower()} and {top[2].lower()}",
           f"Bank of Japan Tankan employment conditions DI, {quarter}, all firm sizes: % of firms with excess staff minus % short of staff.\n"
           "Blue, bold: proposed focus sectors. Dark gray: all industries. Health & social work is not covered by the Tankan.",
           "Source: Bank of Japan, Tankan, via the BOJ time-series API (data/processed/boj_tankan_employment_di.csv)",
           "2_tankan_shortage_by_industry")


def tankan_trend() -> None:
    t = pd.read_csv(PROCESSED / "boj_tankan_employment_di.csv")
    t = t.assign(x=t.period.str[:4].astype(int) + (t.period.str[-1].astype(int) - 1) / 4)
    t = t[t.x >= BASE_YEAR]

    fig = plt.figure(figsize=(10, 5.8))
    ax = fig.add_axes([0.07, 0.11, 0.74, 0.67])
    allind = t[t.sector == "全産業"]
    ax.plot(allind.x, allind.value, color=MUTED, linewidth=1.5)
    ends = {"All industries": allind.value.iloc[-1]}
    for color, (sector, label) in zip(SERIES, FOCUS_TANKAN.items()):
        s = t[t.sector == sector]
        ax.plot(s.x, s.value, color=color, label=label)
        ends[label] = s.value.iloc[-1]
    x_end = t.x.max()
    for label, y in spread(ends, gap=5).items():
        color = MUTED if label == "All industries" else SERIES[list(FOCUS_TANKAN.values()).index(label)]
        ax.plot([x_end + 0.2, x_end + 0.9], [ends[label], y], color=color, linewidth=0.8)
        ax.text(x_end + 1.1, y, f"{label} {ends[label]:.0f}", va="center", fontsize=9, color=INK2)
    ax.axhline(0, color=AXIS, linewidth=1)
    ax.set_xlim(BASE_YEAR, x_end + 0.2)
    ax.set_ylabel("DI (% points)")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(loc="lower left", frameon=False, fontsize=9, ncol=4)
    finish(fig,
           "Since 2013, shortages have deepened most in construction, transport and accommodation & food",
           "Bank of Japan Tankan employment conditions DI, all firm sizes, quarterly. Below zero = more firms short of staff "
           "than with excess staff.\nGray: all industries. Accommodation & food is surveyed from 2004; its 2020–21 spike is "
           "the COVID-19 collapse in demand.",
           "Source: Bank of Japan, Tankan, via the BOJ time-series API (data/processed/boj_tankan_employment_di.csv)",
           "3_tankan_shortage_trend")


def esri_wide(indicator_prefix: str) -> pd.DataFrame:
    e = pd.read_csv(PROCESSED / "esri_by_industry.csv")
    d = e[e.indicator.str.startswith(indicator_prefix) & (e.level == 1)]
    return d.pivot(index="sector", columns="period", values="value"), d.drop_duplicates("sector").set_index("sector").sector_en


def ranked_bars(values: pd.Series, names: pd.Series, fmt: str, xlabel: str, title: str, subtitle: str, name: str,
                reference: tuple[str, float] | None = None) -> None:
    order = values.copy()
    if reference:
        order["__ref__"] = reference[1]
    order = order.sort_values()
    labels = [reference[0] if s == "__ref__" else short(names[s]) for s in order.index]
    colors = [MUTED if s == "__ref__" else HIGHLIGHT if s in FOCUS_ESRI else CONTEXT for s in order.index]
    fig = plt.figure(figsize=(10, 6.6))
    ax = fig.add_axes([0.33, 0.15, 0.6, 0.65])
    ax.barh(labels, order.values, color=colors, height=0.62)
    span = order.max() - min(order.min(), 0)
    for y, v in enumerate(order.values):
        ax.text(v + (span * 0.01 if v >= 0 else -span * 0.01), y, fmt.format(v), va="center",
                ha="left" if v >= 0 else "right", fontsize=8.5, color=INK2)
    for tick, sector in zip(ax.get_yticklabels(), order.index):
        tick.set_fontweight("bold" if sector in FOCUS_ESRI else "normal")
    ax.axvline(0, color=AXIS, linewidth=1)
    ax.set_xlim(min(order.min(), 0) - span * 0.12, order.max() + span * 0.12)
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    finish(fig, title, subtitle,
           "Source: Cabinet Office ESRI national accounts, 2024 annual estimates, 2020 base (data/processed/esri_by_industry.csv)",
           name)


def employment_change() -> None:
    emp, names = esri_wide("Persons employed")
    e = pd.read_csv(PROCESSED / "esri_by_industry.csv")
    total = e[(e.indicator == "Persons employed") & (e.sector == "合計")].set_index("period").value
    change = (emp[LAST_YEAR] / emp[BASE_YEAR] - 1) * 100
    top = change.idxmax()
    ranked_bars(change, names, "{:+.0f}%", f"Change in persons employed, {BASE_YEAR}–{LAST_YEAR} (%)",
                f"Health & social work employment rose {change[top]:.0f}% since {BASE_YEAR}; construction and manufacturing shrank",
                f"Persons employed by industry, calendar years {BASE_YEAR} and {LAST_YEAR}. "
                f"Health & social work: {emp.loc[top, BASE_YEAR] / 100:.1f}m in {BASE_YEAR}, {emp.loc[top, LAST_YEAR] / 100:.1f}m in {LAST_YEAR}.\n"
                "Blue, bold: proposed focus sectors. Dark gray: all industries.",
                "4_employment_change_by_industry",
                reference=("All industries", (total[LAST_YEAR] / total[BASE_YEAR] - 1) * 100))


def productivity_growth() -> None:
    va, names = esri_wide("Real value added")
    persons, _ = esri_wide("Persons employed")
    hours, _ = esri_wide("Hours worked")
    if not 1000 < hours[LAST_YEAR].median() < 2600:
        raise RuntimeError("Hours worked no longer looks like annual hours per person; check the ESRI table")
    per_hour = va / (persons * hours)
    years = LAST_YEAR - BASE_YEAR
    growth = ((per_hour[LAST_YEAR] / per_hour[BASE_YEAR]) ** (1 / years) - 1) * 100
    ranked_bars(growth, names, "{:+.1f}%", f"Average annual growth in real value added per hour worked, {BASE_YEAR}–{LAST_YEAR} (%)",
                "Output per hour fell in accommodation & food and in health & social work; manufacturing rose",
                f"Real value added (chain-linked, 2020 prices) ÷ (persons employed × annual hours per person), by industry, "
                f"{BASE_YEAR}–{LAST_YEAR}.\nBlue, bold: proposed focus sectors. Shortage sectors with flat or falling "
                "productivity cannot easily make up for fewer workers.",
                "5_productivity_growth_by_industry")


def hellowork_ratios() -> None:
    h = pd.read_csv(PROCESSED / "estat_hellowork_by_occupation.csv")
    r = h[h.indicator == "Active openings-to-applicants ratio"]
    lines = [  # colours follow the matching sectors in chart 3
        ("建設・採掘従事者", "Construction & mining", SERIES[0]),
        ("輸送・機械運転従事者/自動車運転従事者", "Motor vehicle drivers", SERIES[1]),
        ("サービス職業従事者/接客・給仕職業従事者", "Waiting & serving staff", SERIES[2]),
        ("介護関係職種", "Care-related occupations", CARE),
    ]
    every = r[r.sector == "職業計"].set_index("period").value
    first, last = int(every.index.min()), int(every.index.max())

    fig = plt.figure(figsize=(10, 5.8))
    ax = fig.add_axes([0.07, 0.11, 0.7, 0.67])
    ax.plot(every.index, every.values, color=MUTED, linewidth=1.5)
    ends, colors = {"All occupations": every.iloc[-1]}, {"All occupations": MUTED}
    for sector, label, color in lines:
        s = r[r.sector == sector].set_index("period").value
        ax.plot(s.index, s.values, color=color, label=label)
        ends[label], colors[label] = s.iloc[-1], color
    for label, y in spread(ends, gap=0.3).items():
        ax.plot([last + 0.1, last + 0.45], [ends[label], y], color=colors[label], linewidth=0.8)
        ax.text(last + 0.55, y, f"{label} {ends[label]:.2f}", va="center", fontsize=9, color=INK2)
    ax.axvline(2022.5, color=AXIS, linewidth=1)
    ax.text(2022.6, 5.9, "Occupation\nclassification\nchanged", fontsize=8, color=MUTED, va="top")
    ax.set_ylim(0, 6)
    ax.set_xlim(first, last + 0.1)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.set_ylabel("Job openings per applicant")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(loc="upper left", frameon=False, fontsize=9, ncol=2)
    care, average = ends["Care-related occupations"], ends["All occupations"]
    finish(fig,
           f"Care work has {care:.1f} job openings per applicant, {care / average:.1f} times the all-occupation average",
           f"Hello Work active openings-to-applicants ratio by occupation, annual average, regular jobs incl. part-time, "
           f"{first}–{last}.\nCare and construction stayed high through COVID-19; driving and serving jobs dipped in "
           "2020–21. Gray: all occupations.",
           "Source: MHLW Employment Referrals (Hello Work listings only) via the e-Stat file catalogue "
           "(data/processed/estat_hellowork_by_occupation.csv)",
           "6_hellowork_openings_per_applicant")


def main() -> None:
    working_age_population()
    tankan_by_industry()
    tankan_trend()
    employment_change()
    productivity_growth()
    hellowork_ratios()


if __name__ == "__main__":
    main()
