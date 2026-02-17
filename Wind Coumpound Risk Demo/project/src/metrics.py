"""
metrics.py
Compute hourly and daily wind-risk metrics.

Metric hierarchy
----------------
  Hourly:
    EWS  — Effective Wind Stress
    CWL_hour  — hourly contribution to Cumulative Wind Load
    SHWe_hour — hourly contribution to Sustained High-Wind Excess (recovery windows only)

  Daily:
    daily_CWL, cumulative_CWL
    daily_SHWe, cumulative_SHWe
    no_recovery_day, consecutive_no_recovery_days
    high_wind_day, failed_recovery_night, compound
    consecutive_high_wind_days, consecutive_failed_recovery_nights, consecutive_compound_cycles
"""

import numpy as np
import pandas as pd

# --- Constants ---
BASELINE_WIND = 20.0        # m/s — daytime load baseline
BASELINE_RECOVERY = 10.0    # m/s — overnight recovery baseline
CWL_HIGH_DAY_THRESHOLD = 50.0
SHWe_FAIL_NIGHT_THRESHOLD = 20.0

# Recovery window hours (inclusive on left, exclusive on right)
RECOVERY_HOURS = frozenset(range(0, 6)) | frozenset(range(22, 24))


# ──────────────────────────────────────────────────────────────────────────────
# Hourly metrics
# ──────────────────────────────────────────────────────────────────────────────

def compute_ews(df: pd.DataFrame) -> pd.Series:
    """Effective Wind Stress (EWS) — blends sustained and gust components."""
    return df["wind_speed_ms"] + 0.3 * (df["gust_ms"] - df["wind_speed_ms"])


def compute_cwl_hour(ews: pd.Series) -> pd.Series:
    """Hourly above-baseline wind load contribution."""
    return (ews - BASELINE_WIND).clip(lower=0)


def compute_shwe_hour(ews: pd.Series) -> pd.Series:
    """
    Hourly above-recovery-baseline excess, but only during overnight
    recovery windows (00:00–06:00 and 22:00–24:00 local hour).
    """
    in_recovery = ews.index.hour.isin(RECOVERY_HOURS)
    excess = (ews - BASELINE_RECOVERY).clip(lower=0)
    return excess.where(in_recovery, other=0.0)


# ──────────────────────────────────────────────────────────────────────────────
# Daily aggregation helpers
# ──────────────────────────────────────────────────────────────────────────────

def _streak(bool_series: pd.Series) -> pd.Series:
    """Running streak of consecutive True values (resets to 0 on False)."""
    streak = []
    count = 0
    for val in bool_series:
        count = count + 1 if val else 0
        streak.append(count)
    return pd.Series(streak, index=bool_series.index)


def compute_daily_metrics(hourly: pd.DataFrame) -> pd.DataFrame:
    """
    Given an hourly DataFrame (with EWS, CWL_hour, SHWe_hour columns),
    return a daily summary DataFrame.
    """
    date_key = hourly.index.normalize()   # truncate to midnight UTC

    # --- daily CWL and SHWe sums ---
    daily_cwl = hourly["CWL_hour"].groupby(date_key).sum().rename("daily_CWL")
    daily_shwe = hourly["SHWe_hour"].groupby(date_key).sum().rename("daily_SHWe")

    # --- no-recovery day: max EWS during recovery windows exceeds baseline ---
    rec_mask = hourly.index.hour.isin(RECOVERY_HOURS)
    ews_recovery = hourly.loc[rec_mask, "EWS"]
    max_ews_recovery = ews_recovery.groupby(ews_recovery.index.normalize()).max()
    max_ews_recovery = max_ews_recovery.reindex(daily_cwl.index, fill_value=0.0)
    no_recovery_day = (max_ews_recovery > BASELINE_RECOVERY).rename("no_recovery_day")

    # --- compound flags ---
    high_wind_day = (daily_cwl > CWL_HIGH_DAY_THRESHOLD).rename("high_wind_day")
    failed_recovery_night = (daily_shwe > SHWe_FAIL_NIGHT_THRESHOLD).rename("failed_recovery_night")
    compound = (high_wind_day & failed_recovery_night).rename("compound")

    # --- cumulative series ---
    cumulative_cwl = daily_cwl.cumsum().rename("cumulative_CWL")
    cumulative_shwe = daily_shwe.cumsum().rename("cumulative_SHWe")

    # --- streaks ---
    consecutive_no_recovery = _streak(no_recovery_day).rename("consecutive_no_recovery_days")
    consecutive_high_wind = _streak(high_wind_day).rename("consecutive_high_wind_days")
    consecutive_failed_recovery = _streak(failed_recovery_night).rename("consecutive_failed_recovery_nights")
    consecutive_compound = _streak(compound).rename("consecutive_compound_cycles")

    daily = pd.concat(
        [
            daily_cwl,
            daily_shwe,
            cumulative_cwl,
            cumulative_shwe,
            no_recovery_day,
            high_wind_day,
            failed_recovery_night,
            compound,
            consecutive_no_recovery,
            consecutive_high_wind,
            consecutive_failed_recovery,
            consecutive_compound,
        ],
        axis=1,
    )
    daily.index.name = "date"
    return daily


# ──────────────────────────────────────────────────────────────────────────────
# Top-level entry point
# ──────────────────────────────────────────────────────────────────────────────

def compute_all(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute all hourly and daily metrics.

    Parameters
    ----------
    df : pd.DataFrame
        Raw hourly DataFrame from data_loader.load().

    Returns
    -------
    hourly : pd.DataFrame  — original columns + EWS, CWL_hour, SHWe_hour
    daily  : pd.DataFrame  — daily aggregated metrics
    """
    hourly = df.copy()
    hourly["EWS"] = compute_ews(hourly)
    hourly["CWL_hour"] = compute_cwl_hour(hourly["EWS"])
    hourly["SHWe_hour"] = compute_shwe_hour(hourly["EWS"])

    daily = compute_daily_metrics(hourly)
    return hourly, daily
