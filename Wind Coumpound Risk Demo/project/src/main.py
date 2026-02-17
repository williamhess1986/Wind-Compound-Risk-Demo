"""
main.py
Entry point for the Extreme Wind Compound Risk Demo.

Usage
-----
    python src/main.py                        # runs all three sample datasets
    python src/main.py --csv path/to/my.csv   # runs a single custom CSV
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# ── ensure src/ is on path when running as a script ───────────────────────────
SRC_DIR = Path(__file__).parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import data_loader
import metrics
import risk_states
import visualization

PROJECT_ROOT = SRC_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

SAMPLE_DATASETS = {
    "Cyclone Event": DATA_DIR / "sample_cyclone_event.csv",
    "Fire-Weather Period": DATA_DIR / "sample_wind_fireweather.csv",
    "Future +10% Scenario": DATA_DIR / "sample_future_plus10pct_winds.csv",
}

SUMMARY_COLS = [
    "daily_CWL",
    "daily_SHWe",
    "compound",
    "consecutive_compound_cycles",
    "risk_state",
    "risk_multiplier",
]


# ── helpers ────────────────────────────────────────────────────────────────────

def _print_banner(text: str) -> None:
    print("\n" + "═" * 70)
    print(f"  {text}")
    print("═" * 70)


def _print_summary(daily: pd.DataFrame, label: str) -> None:
    _print_banner(f"Summary — {label}")
    display = daily[SUMMARY_COLS].copy()
    display.index = display.index.strftime("%Y-%m-%d")
    display["daily_CWL"] = display["daily_CWL"].round(1)
    display["daily_SHWe"] = display["daily_SHWe"].round(1)
    display["risk_multiplier"] = display["risk_multiplier"].round(3)
    print(display.to_string())


# ── main logic ─────────────────────────────────────────────────────────────────

def run_dataset(csv_path: Path, label: str) -> None:
    """
    Full pipeline for a single CSV:
    load → compute metrics → classify risk → visualise → print summary.
    """
    print(f"\n▶  Processing: {label}  ({csv_path.name})")

    # 1. Load
    df = data_loader.load(csv_path)
    print(f"   Loaded {len(df):,} hourly rows  "
          f"({df.index.min().date()} → {df.index.max().date()})")

    # 2. Metrics
    hourly, daily = metrics.compute_all(df)

    # 3. Risk states
    daily = risk_states.compute_risk_states(daily)

    # 4. Visualise (saves PNG to /output)
    visualization.plot_all(hourly, daily, title_prefix=label, output_dir=OUTPUT_DIR)

    # 5. Print summary
    _print_summary(daily, label)

    # 6. Save daily CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_label = label.replace(" ", "_").replace("/", "-")
    daily_out = OUTPUT_DIR / f"{safe_label}_daily_metrics.csv"
    daily.to_csv(daily_out)
    print(f"  ✔ Saved daily metrics → {daily_out}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extreme Wind Compound Risk Demo"
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Path to a custom CSV file (overrides the three sample datasets).",
    )
    parser.add_argument(
        "--label",
        type=str,
        default="Custom Dataset",
        help="Label for the custom CSV (used in titles and filenames).",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.csv is not None:
        run_dataset(args.csv, args.label)
    else:
        for label, path in SAMPLE_DATASETS.items():
            run_dataset(path, label)

    print("\n✅  All done.  Outputs written to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
