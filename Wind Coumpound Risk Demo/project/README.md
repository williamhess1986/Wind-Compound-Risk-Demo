# Extreme Wind Compound Risk Demo

> **Beyond peak gusts: recovery windows and system margins matter more.**

A single catastrophic gust is dramatic, but the real driver of infrastructure and ecosystem failure is *persistence*. When overnight winds stay too high for hours to recover, day after day, cumulative strain accumulates non-linearly — much like fluid drag scales with the *square* of velocity. This tool makes that compounding visible.

---

## Contents

```
project/
├── src/
│   ├── data_loader.py      # CSV ingestion & validation
│   ├── metrics.py          # EWS, CWL, SHWe, compound streak logic
│   ├── risk_states.py      # Risk-state classification + escalation multiplier
│   ├── visualization.py    # Five-panel Matplotlib figure
│   └── main.py             # CLI entry point
├── data/
│   ├── sample_cyclone_event.csv
│   ├── sample_wind_fireweather.csv
│   └── sample_future_plus10pct_winds.csv
├── notebooks/
│   └── demo.ipynb          # Interactive walkthrough
├── output/                 # Auto-created on first run
├── generate_sample_data.py # Regenerate synthetic CSVs
├── requirements.txt
├── LICENSE
└── README.md               # You are here
```

---

## Conceptual Framework

### The problem with peak-gust thinking

Standard warnings focus on maximum gust speed. That matters for acute structural failure — but most real-world damage accumulates through **sustained loading** and **disrupted recovery**. A forest, power grid, or human body subjected to 40 m/s winds for three consecutive days without a calm night is more compromised than one that experienced a brief 55 m/s spike followed by recovery.

This tool quantifies both dimensions:

1. **How much daytime load accumulated?** → Cumulative Wind Load (CWL)
2. **Did nights provide genuine recovery?** → Sustained High-Wind Excess (SHWe)
3. **Are the two co-occurring?** → Compound Strain

---

## Metric Definitions

### Effective Wind Stress (EWS)

```
EWS = wind_speed_ms + 0.3 × (gust_ms − wind_speed_ms)
```

Blends the sustained wind with a 30 % contribution from the gust excess. This approximates the *effective* mechanical load: gusts add impulse; sustained wind adds fatigue.

---

### Cumulative Wind Load (CWL)

```
baseline_wind = 20.0 m/s            # below this, negligible structural load
CWL_hour      = max(EWS − 20.0, 0)  # hourly above-baseline contribution
daily_CWL     = Σ CWL_hour per day
cumulative_CWL = running sum
```

Think of it as *wind-load degree-hours* — analogous to heating-degree-days in energy modelling.  
A daily CWL of 80 means the wind averaged 23.3 m/s above the 20 m/s baseline across the full day.

---

### Sustained High-Wind Excess (SHWe) — the recovery window metric

```
recovery_window = hours 00:00–06:00 and 22:00–24:00
baseline_recovery = 10.0 m/s

SHWe_hour  = max(EWS − 10.0, 0)   (only during recovery windows)
daily_SHWe = Σ SHWe_hour per day
cumulative_SHWe = running sum
```

If EWS stays above 10 m/s all night, the system never gets the low-stress window it needs. SHWe quantifies *how much* recovery was stolen.

Complementary boolean:

```
no_recovery_day = max(EWS in recovery windows) > 10.0
consecutive_no_recovery_days = running streak
```

---

### Compound Strain

```
high_wind_day        = daily_CWL  > 50.0
failed_recovery_night = daily_SHWe > 20.0
compound             = high_wind_day AND failed_recovery_night

consecutive_compound_cycles = running streak of compound days
```

A compound event is more dangerous than either component alone because the system enters each new day *already weakened* from the previous night's failure to recover.

---

## Risk States

| State      | Condition                                                                     |
|------------|-------------------------------------------------------------------------------|
| **Stable** | `daily_CWL < 80` AND `daily_SHWe < 40` AND `compound_streak < 2`            |
| **Straining** | `daily_CWL ≥ 80` OR `daily_SHWe ≥ 40` OR `compound_streak ≥ 2`           |
| **Failure** | `daily_CWL ≥ 160` OR `daily_SHWe ≥ 80` OR `compound_streak ≥ 4`           |

Failure takes precedence over Straining.

---

## Nonlinear Escalation

```
risk_multiplier = 1 + (CWL / 80) + (SHWe / 40) + (compound_streak × 0.5)
```

This mirrors the physics of fluid drag — force scales with velocity squared, so moderate sustained winds above the threshold contribute disproportionately to structural fatigue. The compound streak term adds a "memory" component: each additional day without recovery is costlier than the last.

| Multiplier | Interpretation                        |
|-----------|---------------------------------------|
| 1.0       | Baseline — no excess load             |
| 2.0       | Straining — sustained excess          |
| 4.0       | Failure — severe compound event       |
| 10–20+    | Extreme multi-day cyclone peak        |

---

## Visualisations

The pipeline generates a five-panel figure for each dataset:

| Panel | Content |
|-------|---------|
| 1 | Hourly `wind_speed_ms`, `gust_ms`, `EWS`; baseline reference lines |
| 2 | `cumulative_CWL` curve |
| 3 | `daily_SHWe` bar chart (colour-coded by risk state) |
| 4 | Daily risk-state band (green / amber / red) |
| 5 | Nonlinear escalation gauge (`risk_multiplier`) |

---

## Installation

```bash
git clone https://github.com/your-org/wind-compound-risk.git
cd wind-compound-risk
pip install -r requirements.txt
```

---

## Running the demo

```bash
# Run all three sample datasets
python src/main.py

# Run a single custom CSV
python src/main.py --csv path/to/my_data.csv --label "My Event"
```

Outputs are written to `output/`:

- `<dataset>_panels.png` — five-panel figure
- `<dataset>_daily_metrics.csv` — full daily table

---

## Using your own CSV

Your CSV must include these columns:

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | ISO 8601 string | e.g. `2024-03-01T00:00:00Z` |
| `wind_speed_ms` | float | 10-min mean wind speed (m/s) |
| `gust_ms` | float | Peak gust in the hour (m/s) |

Optional columns (used if present):

| Column | Type | Range |
|--------|------|-------|
| `rainfall_mm` | float | ≥ 0 |
| `fuel_dryness_index` | float | 0–1 |
| `infrastructure_vulnerability` | float | 0–1 |

Hourly data is recommended. Sub-hourly data is supported but aggregation is not performed automatically — resample to hourly before loading if needed.

---

## Interactive notebook

```bash
jupyter notebook notebooks/demo.ipynb
```

The notebook walks through each pipeline step with inline commentary.

---

## Regenerating sample data

```bash
python generate_sample_data.py
```

---

## License

MIT — see `LICENSE`.
