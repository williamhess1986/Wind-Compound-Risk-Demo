# Wind Compound Risk Demo

## Overview

This project demonstrates a simple framework for understanding **compound wind risk** using hourly wind observations.

Rather than focusing only on peak gusts, the model emphasizes what actually drives real-world impacts:

* persistence of damaging winds
* failure of calm recovery periods
* multi-day mechanical fatigue
* nonlinear escalation of wind forces

The goal is **public literacy and conceptual clarity**, not forecasting.

It shows how infrastructure damage often results from sustained strain across multiple days — not just one extreme gust.

---

## Core Idea

Wind damage rarely comes from a single peak gust.

Instead, impacts typically occur when:

* Strong winds persist for long durations
* Calm periods are too short for recovery
* Multiple days of mechanical loading stack
* Rain or soil saturation weakens anchors

This demo models that dynamic using simple, interpretable metrics.

---

## Metrics Computed from Hourly Data

Given a CSV of hourly observations, the app computes daily wind-strain indicators.

All hourly excess values are expressed in **(m/s·hr)**.

---

### 1. Effective Wind Stress (EWS)

A proxy for aerodynamic load combining sustained wind and gust effects.

```
EWS = wind_speed_ms + 0.5 * gust_speed_ms
```

If gust data is unavailable:

```
EWS = wind_speed_ms
```

This represents the combined sustained and peak mechanical loading experienced by structures and vegetation.

---

### 2. Cumulative Wind Load (CWL)

Measures how much damaging wind stress accumulates during the day.

```
baseline_wind = damaging wind threshold
CWL_hour = max(EWS - baseline_wind, 0)
daily_CWL = sum(CWL_hour)
cumulative_CWL = running sum
```

The baseline typically represents:

* onset of tree damage (~15–20 m/s sustained), or
* power-line stress thresholds

CWL reflects **fatigue loading over time**, not just peak gust intensity.

---

### 3. Sustained High-Wind Excess (SHWe)

Captures failure of calm recovery periods.

This is a critical driver of compound wind damage.

```
calm_threshold = 10 m/s
SHWe_hour = max(wind_speed_ms - calm_threshold, 0)
daily_SHWe = sum over recovery window (20:00–08:00)
cumulative_SHWe = running sum
```

The recovery window approximates periods when winds normally subside.

SHWe measures how long systems remain under continuous stress without relief.

---

### 4. Compound Wind Strain

A compound wind cycle occurs when:

```
high_wind_day = daily_CWL > threshold_CWL
poor_recovery_night = daily_SHWe > threshold_SHWe
compound = high_wind_day AND poor_recovery_night
```

The model tracks streaks of:

* consecutive damaging wind days
* consecutive recovery failures
* consecutive compound wind cycles

These streaks represent **mechanical fatigue accumulation**.

---

## Risk States (Daily Operational Classification)

Risk is evaluated **per day**, based on current strain and persistence — not long-term rarity.

```
Stable:
  low daily_CWL
  low daily_SHWe
  short or no streaks

Straining:
  moderate daily wind accumulation
  or multiple consecutive compound cycles

Failure:
  high daily excess
  or prolonged compound streaks
```

This reflects how real wind damage emerges: from sustained loading and insufficient recovery between events.

---

## Nonlinear Escalation Gauge

Wind forces increase nonlinearly due to aerodynamic drag.

Damage potential scales approximately with **wind speed squared (v²)**.

The demo includes a simple multiplier illustrating this rapid escalation:

```
risk_multiplier =
  1
  + (daily_CWL / norm_CWL)
  + (daily_SHWe / norm_SHWe)
  + (compound_streak * factor)
```

This captures how risk can ramp quickly once persistence begins.

---

## Visualizations

The app generates five panels:

### Timeline

Wind speed and effective wind stress over time with baseline reference.

### CWL Curve

Accumulated daytime wind load across days.

### SHWe Bars

Nighttime recovery failure intensity.

### Risk State Band

Color-coded operational risk:

* Green = Stable
* Amber = Straining
* Red = Failure

### Nonlinear Escalation Gauge

Shows how compound wind strain accelerates risk.

Outputs are saved as **PNG and interactive HTML** in `/output`.

---

## Input CSV Format

Required columns:

```
timestamp (ISO8601)
wind_speed_ms (float)
```

Optional columns:

```
gust_speed_ms
wind_direction_deg
rainfall_mm
```

Rainfall can act as an optional compound factor by weakening soil anchoring and increasing damage susceptibility.

---

## Sample Datasets

Synthetic datasets included:

* Historical nor’easter scenario
* Multi-day extratropical storm sequence
* Future intensified cyclone scenario

These illustrate how sustained wind persistence drives compound risk.

---

## Why This Matters

Wind risk is often communicated as a peak gust value.

But real damage depends on:

* duration of loading
* lack of calm recovery periods
* multi-day fatigue effects
* nonlinear force escalation

The greatest danger is not a single extreme gust.

It is **persistent damaging winds without recovery**.

This demo illustrates how simple accumulation metrics can reveal that risk early.

---

## How to Run

Install dependencies:

```
pip install -r requirements.txt
```

Run the demo:

```
python src/main.py
```

To use your own data:

```
python src/main.py data/your_file.csv
```

Your CSV must follow the input schema above.

---

## Purpose

This is not a forecasting or engineering model.

It is a **conceptual and public-literacy tool** designed to help users understand compound wind risk and the role of persistence in real-world damage.

---

## License

MIT License — free to use, modify, and build upon.
