"""
visualization.py
Generate all five analysis panels for a wind-risk dataset.

Panel 1 — Wind timeline (wind_speed_ms, gust_ms, EWS, baseline lines)
Panel 2 — Cumulative Wind Load curve
Panel 3 — Daily SHWe bar chart
Panel 4 — Risk state band (colour-coded)
Panel 5 — Nonlinear escalation gauge (risk_multiplier)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from risk_states import STATE_COLORS

# ── colour palette ─────────────────────────────────────────────────────────────
C_WIND = "#2196F3"
C_GUST = "#90CAF9"
C_EWS = "#FF5722"
C_CWL = "#7B1FA2"
C_SHWE = "#F57C00"
BASELINE_STYLE = dict(color="#546E7A", linestyle="--", linewidth=1.0, alpha=0.7)

STATE_PATCH_ALPHA = 0.35
STATE_CMAP = {
    "Stable": "#4CAF50",
    "Straining": "#FFC107",
    "Failure": "#F44336",
}


# ── helpers ────────────────────────────────────────────────────────────────────

def _shade_risk_band(ax: plt.Axes, daily: pd.DataFrame) -> None:
    """Shade background of an axes by daily risk state."""
    for row in daily.itertuples():
        color = STATE_CMAP.get(row.risk_state, "#FFFFFF")
        ax.axvspan(
            pd.Timestamp(row.Index) - pd.Timedelta(hours=12),
            pd.Timestamp(row.Index) + pd.Timedelta(hours=12),
            color=color,
            alpha=0.12,
            linewidth=0,
        )


def _legend_patches() -> list[mpatches.Patch]:
    return [
        mpatches.Patch(facecolor=STATE_CMAP[s], alpha=STATE_PATCH_ALPHA, label=s)
        for s in ["Stable", "Straining", "Failure"]
    ]


# ── main plot function ─────────────────────────────────────────────────────────

def plot_all(
    hourly: pd.DataFrame,
    daily: pd.DataFrame,
    title_prefix: str = "",
    output_dir: str | Path | None = None,
) -> plt.Figure:
    """
    Build all five analysis panels and optionally save to disk.

    Parameters
    ----------
    hourly : pd.DataFrame
        Hourly metrics (from metrics.compute_all).
    daily  : pd.DataFrame
        Daily metrics with risk_state / risk_multiplier columns.
    title_prefix : str
        Prepended to each panel title (e.g. dataset name).
    output_dir : path-like, optional
        If supplied the figure is saved as <output_dir>/<title_prefix>_panels.png

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, axes = plt.subplots(5, 1, figsize=(14, 22), sharex=False)
    fig.suptitle(
        f"{title_prefix} — Extreme Wind Compound Risk Analysis",
        fontsize=14,
        fontweight="bold",
        y=0.995,
    )

    date_range = (hourly.index.min(), hourly.index.max())

    # ── Panel 1: wind timeline ─────────────────────────────────────────────────
    ax = axes[0]
    ax.fill_between(hourly.index, 0, hourly["gust_ms"], color=C_GUST, alpha=0.4, label="Gust (m/s)")
    ax.plot(hourly.index, hourly["wind_speed_ms"], color=C_WIND, linewidth=1.2, label="Wind Speed (m/s)")
    ax.plot(hourly.index, hourly["EWS"], color=C_EWS, linewidth=1.4, linestyle="-", label="EWS (m/s)")
    ax.axhline(20.0, label="Baseline wind (20 m/s)", **BASELINE_STYLE)
    ax.axhline(10.0, label="Recovery baseline (10 m/s)", color="#B0BEC5", linestyle=":", linewidth=1.0)
    _shade_risk_band(ax, daily)
    ax.set_ylabel("Wind speed (m/s)")
    ax.set_title(f"{title_prefix}  |  Panel 1 — Hourly Wind, Gust & EWS")
    ax.legend(loc="upper right", fontsize=8, ncol=3)
    ax.set_xlim(*date_range)

    # ── Panel 2: cumulative CWL ────────────────────────────────────────────────
    ax = axes[1]
    ax.plot(daily.index, daily["cumulative_CWL"], color=C_CWL, linewidth=2.0, marker="o", markersize=3)
    ax.fill_between(daily.index, 0, daily["cumulative_CWL"], color=C_CWL, alpha=0.15)
    ax.set_ylabel("Cumulative CWL (m/s·h)")
    ax.set_title("Panel 2 — Cumulative Wind Load (CWL)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.set_xlim(daily.index.min(), daily.index.max())

    # ── Panel 3: daily SHWe bars ───────────────────────────────────────────────
    ax = axes[2]
    colors_bar = [STATE_CMAP.get(s, "#78909C") for s in daily["risk_state"]]
    ax.bar(daily.index, daily["daily_SHWe"], color=colors_bar, alpha=0.85, width=0.8)
    ax.axhline(20.0, color=C_SHWE, linestyle="--", linewidth=1.2, label="SHWe fail threshold (20)")
    ax.axhline(40.0, color="#E53935", linestyle=":", linewidth=1.2, label="SHWe strain threshold (40)")
    ax.set_ylabel("Daily SHWe (m/s·h)")
    ax.set_title("Panel 3 — Daily Sustained High-Wind Excess (SHWe)")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_xlim(daily.index.min() - pd.Timedelta(days=0.5),
                daily.index.max() + pd.Timedelta(days=0.5))

    # ── Panel 4: risk state band ───────────────────────────────────────────────
    ax = axes[3]
    state_num = daily["risk_state_num"].values.astype(float)
    ax.step(daily.index, state_num, where="mid", color="#37474F", linewidth=1.5)
    for i, row in enumerate(daily.itertuples()):
        ax.bar(
            row.Index,
            1,
            bottom=row.risk_state_num,
            width=0.9,
            color=STATE_CMAP.get(row.risk_state, "#90A4AE"),
            alpha=0.75,
        )
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(["Stable", "Straining", "Failure"])
    ax.set_ylim(-0.1, 3.0)
    ax.set_title("Panel 4 — Daily Risk State")
    ax.legend(handles=_legend_patches(), loc="upper right", fontsize=8, ncol=3)
    ax.set_xlim(daily.index.min() - pd.Timedelta(days=0.5),
                daily.index.max() + pd.Timedelta(days=0.5))

    # ── Panel 5: escalation gauge ──────────────────────────────────────────────
    ax = axes[4]
    rm = daily["risk_multiplier"].values
    threshold_2 = 2.0
    threshold_4 = 4.0
    bar_colors = [
        STATE_CMAP["Failure"] if v >= threshold_4
        else STATE_CMAP["Straining"] if v >= threshold_2
        else STATE_CMAP["Stable"]
        for v in rm
    ]
    ax.bar(daily.index, rm, color=bar_colors, alpha=0.85, width=0.8)
    ax.axhline(1.0, color="#546E7A", linestyle="--", linewidth=1.0, alpha=0.7, label="Baseline (1.0)")
    ax.axhline(threshold_2, color=STATE_CMAP["Straining"], linestyle="--", linewidth=1.2, label=f"Straining ({threshold_2}×)")
    ax.axhline(threshold_4, color=STATE_CMAP["Failure"], linestyle="--", linewidth=1.2, label=f"Failure ({threshold_4}×)")
    ax.set_ylabel("Risk Multiplier (×)")
    ax.set_title("Panel 5 — Nonlinear Escalation Gauge (Risk Multiplier)")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_xlim(daily.index.min() - pd.Timedelta(days=0.5),
                daily.index.max() + pd.Timedelta(days=0.5))

    fig.autofmt_xdate(rotation=30, ha="right")
    fig.tight_layout(rect=[0, 0, 1, 0.995])

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_prefix = title_prefix.replace(" ", "_").replace("/", "-")
        out_path = output_dir / f"{safe_prefix}_panels.png"
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        print(f"  ✔ Saved figure → {out_path}")

    return fig
