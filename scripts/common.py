"""Shared paths and helpers for the Japan data pipeline."""
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
CHARTS = ROOT / "charts"

# Every processed file uses this long layout so sources can be stacked.
# level: 0 = total, 1 = top-level sector, 2+ = sub-sector. sector holds a "parent/child" path below level 1.
TIDY_COLUMNS = ["source", "indicator", "sector", "sector_en", "level", "period", "value", "unit"]


def get(url: str, attempts: int = 3, **kwargs) -> requests.Response:
    """GET with retries on timeouts and connection errors (the World Bank API is sometimes very slow)."""
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, timeout=120, **kwargs)
            response.raise_for_status()
            return response
        except (requests.Timeout, requests.ConnectionError) as error:
            if attempt == attempts:
                raise
            print(f"  retry {attempt}/{attempts - 1} after {type(error).__name__}: {url}")
            time.sleep(15 * attempt)


def download(url: str, path: Path) -> Path:
    """Stream url to path, skipping the download if the file is already there."""
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".part")
    with requests.get(url, stream=True, timeout=300) as response:
        response.raise_for_status()
        with open(partial, "wb") as f:
            for chunk in response.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    partial.rename(path)
    return path


def save_tidy(df: pd.DataFrame, name: str) -> Path:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    path = PROCESSED / f"{name}.csv"
    df[TIDY_COLUMNS].to_csv(path, index=False)
    print(f"wrote {path.relative_to(ROOT)} ({len(df):,} rows)")
    return path
