"""
risk_states.py
Assign daily risk states and compute the nonlinear escalation multiplier.

Risk-state thresholds
---------------------
  Stable   : CWL < 80   AND  SHWe < 40   AND  compound_streak < 2
  Straining: CWL >= 80  OR   SHWe >= 40  OR   compound_streak >= 2
  Failure  : CWL >= 160 OR   SHWe >= 80  OR   compound_streak >= 4

The Failure gate takes precedence over Straining.

Nonlinear escalation multiplier
--------------------------------
  risk_multiplier = 1 + (CWL / 80) + (SHWe / 40) + (compound_streak * 0.5)
"""

import pandas as pd

# Threshold constants
CWL_STRAIN = 80.0
CWL_FAIL = 160.0
SHWE_STRAIN = 40.0
SHWE_FAIL = 80.0
COMPOUND_STRAIN = 2
COMPOUND_FAIL = 4

STATES = ("Stable", "Straining", "Failure")
STATE_COLORS = {"Stable": "green", "Straining": "orange", "Failure": "red"}
STATE_NUM = {"Stable": 0, "Straining": 1, "Failure": 2}


def classify_risk_state(cwl: float, shwe: float, compound_streak: int) -> str:
    """Return risk state string for a single day."""
    if cwl >= CWL_FAIL or shwe >= SHWE_FAIL or compound_streak >= COMPOUND_FAIL:
        return "Failure"
    if cwl >= CWL_STRAIN or shwe >= SHWE_STRAIN or compound_streak >= COMPOUND_STRAIN:
        return "Straining"
    return "Stable"


def risk_multiplier(cwl: float, shwe: float, compound_streak: int) -> float:
    """Nonlinear escalation gauge value."""
    return 1.0 + (cwl / 80.0) + (shwe / 40.0) + (compound_streak * 0.5)


def compute_risk_states(daily: pd.DataFrame) -> pd.DataFrame:
    """
    Append `risk_state` and `risk_multiplier` columns to the daily DataFrame.

    Parameters
    ----------
    daily : pd.DataFrame
        Output of metrics.compute_daily_metrics().

    Returns
    -------
    pd.DataFrame
        Same DataFrame with two additional columns.
    """
    out = daily.copy()

    out["risk_state"] = [
        classify_risk_state(row.daily_CWL, row.daily_SHWe, row.consecutive_compound_cycles)
        for row in out.itertuples()
    ]

    out["risk_multiplier"] = [
        risk_multiplier(row.daily_CWL, row.daily_SHWe, row.consecutive_compound_cycles)
        for row in out.itertuples()
    ]

    out["risk_state_num"] = out["risk_state"].map(STATE_NUM)

    return out
