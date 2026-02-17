"""
generate_sample_data.py
Generates the three synthetic CSV datasets for the wind-risk demo.
Run once from the project root: python generate_sample_data.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(42)


def _hours(start: str, days: int) -> pd.DatetimeIndex:
    return pd.date_range(start=start, periods=days * 24, freq="h", tz="UTC")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Multi-day cyclone event  (8 days)
# ─────────────────────────────────────────────────────────────────────────────

def make_cyclone(start="2024-03-01", days=8):
    idx = _hours(start, days)
    n = len(idx)
    hours = np.arange(n)

    # Wind envelope: ramp up to ~50 m/s at peak (day 3-4), then decay
    peak_hour = int(days * 24 * 0.40)
    envelope = 8 + 44 * np.exp(-((hours - peak_hour) ** 2) / (2 * (24 * 1.5) ** 2))

    # Diurnal modulation (stronger in afternoon)
    hour_of_day = idx.hour.values
    diurnal = 1 + 0.08 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)

    wind = envelope * diurnal + rng.normal(0, 1.5, n)
    wind = np.clip(wind, 0, None)

    gust_factor = 1.25 + 0.15 * rng.random(n)
    gust = wind * gust_factor + rng.normal(0, 2, n)
    gust = np.maximum(gust, wind)

    # Rainfall: heavy near peak
    rain_base = 5 * np.exp(-((hours - peak_hour) ** 2) / (2 * (24 * 1.2) ** 2))
    rainfall = rain_base * (1 + rng.exponential(1, n)) * (wind / envelope.max())
    rainfall = np.clip(rainfall, 0, 60)

    df = pd.DataFrame({
        "timestamp": idx,
        "wind_speed_ms": np.round(wind, 2),
        "gust_ms": np.round(gust, 2),
        "rainfall_mm": np.round(rainfall, 2),
    })
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 2. Fire-weather: dry + windy (7 days)
# ─────────────────────────────────────────────────────────────────────────────

def make_fireweather(start="2024-11-15", days=7):
    idx = _hours(start, days)
    n = len(idx)
    hour_of_day = idx.hour.values

    # Strong daytime winds, weaker nights
    day_wind = 18 + 14 * np.sin(np.pi * np.clip(hour_of_day - 8, 0, 12) / 12)
    trend = 1 + 0.04 * (np.arange(n) / 24)  # slow intensification
    wind = day_wind * trend + rng.normal(0, 2, n)
    wind = np.clip(wind, 2, None)

    gust_factor = 1.30 + 0.20 * rng.random(n)
    gust = wind * gust_factor + rng.normal(0, 1.5, n)
    gust = np.maximum(gust, wind)

    # Very dry conditions
    fdi = 0.75 + 0.20 * rng.random(n)
    fdi = np.clip(fdi, 0, 1)

    # Tiny or zero rainfall
    rainfall = np.clip(rng.exponential(0.3, n), 0, 3)

    df = pd.DataFrame({
        "timestamp": idx,
        "wind_speed_ms": np.round(wind, 2),
        "gust_ms": np.round(gust, 2),
        "rainfall_mm": np.round(rainfall, 3),
        "fuel_dryness_index": np.round(fdi, 3),
        "infrastructure_vulnerability": np.round(0.4 + 0.3 * rng.random(n), 3),
    })
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 3. Future +10 % scenario (same base as cyclone, scaled up)
# ─────────────────────────────────────────────────────────────────────────────

def make_future(start="2024-03-01", days=8, scale=1.10):
    df = make_cyclone(start, days).copy()
    df["wind_speed_ms"] = np.round(df["wind_speed_ms"] * scale, 2)
    df["gust_ms"] = np.round(df["gust_ms"] * scale, 2)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Write to disk
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cyclone = make_cyclone()
    cyclone.to_csv(DATA_DIR / "sample_cyclone_event.csv", index=False)
    print(f"✔  Cyclone dataset      ({len(cyclone)} rows)")

    fireweather = make_fireweather()
    fireweather.to_csv(DATA_DIR / "sample_wind_fireweather.csv", index=False)
    print(f"✔  Fire-weather dataset ({len(fireweather)} rows)")

    future = make_future()
    future.to_csv(DATA_DIR / "sample_future_plus10pct_winds.csv", index=False)
    print(f"✔  Future +10 % dataset ({len(future)} rows)")

    print("\nAll sample CSVs written to:", DATA_DIR)
