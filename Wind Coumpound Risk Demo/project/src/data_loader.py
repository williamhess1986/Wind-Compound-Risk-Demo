"""
data_loader.py
Load and validate wind-risk CSVs.
"""

import pandas as pd
from pathlib import Path

REQUIRED_COLS = {"timestamp", "wind_speed_ms", "gust_ms"}
OPTIONAL_COLS = {"rainfall_mm", "fuel_dryness_index", "infrastructure_vulnerability"}


def load(path: str | Path) -> pd.DataFrame:
    """
    Load a wind-risk CSV, validate schema, parse timestamps, and return a
    clean DataFrame sorted by time with a DatetimeIndex.

    Parameters
    ----------
    path : str or Path
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
        Validated, sorted DataFrame.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    df = pd.read_csv(path)

    # --- validate required columns ---
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    # --- parse timestamps ---
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp").reset_index(drop=True)
    df = df.set_index("timestamp")

    # --- coerce numeric types ---
    numeric_cols = (REQUIRED_COLS | OPTIONAL_COLS) & set(df.columns)
    numeric_cols.discard("timestamp")
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- basic range checks ---
    if (df["wind_speed_ms"] < 0).any():
        raise ValueError("wind_speed_ms contains negative values.")
    if (df["gust_ms"] < 0).any():
        raise ValueError("gust_ms contains negative values.")

    return df
