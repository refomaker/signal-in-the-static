# Signal in the Static — Executed Computational Validation
All numbers below were **actually computed** by the attached Python scripts (`src/model.py`, `src/simulate.py`, `src/plots.py`), not estimated by hand. Every input is labeled REAL_OBS / DERIVED / INTERPOLATION / EXTRAPOLATION / ASSUMPTION / SIMULATED per the rules set in this validation chain.

## 1. Physical model actually used

Two literature anchor points were used to fit a 2-point power-law frequency model (nothing more sophisticated is supportable by the available field-measurement literature, which never sweeps one storm across 14–73.5 GHz):

- **Haddad (1983), 9.4 GHz, wet dust (10% moisture): 0.8 dB/km** — REAL_OBS
- **Port Sudan field study, 18 GHz, severe storm (visibility <50 m), >16 dB over 4.86 km → 3.292 dB/km** — REAL_OBS/DERIVED

Fitted exponent: **n = 2.177** (A(f) = A_ref·(f/f_ref)^n). This is an INTERPOLATION between 9.4–18 GHz and an **EXTRAPOLATION** above 18 GHz.

**Critical finding from running the model:** extrapolating this simple power-law to 40 GHz and 73.5 GHz under "severe" conditions produces **18.7 dB/km and 70.5 dB/km** respectively — the 73.5 GHz figure implies >350 dB of total attenuation over just a 5 km link, which is **physically implausible** (would represent total signal blackout at almost any realistic link length). This is an honest, computed result showing the naive 2-point extrapolation **breaks down above ~22 GHz** and should not be trusted numerically there — only directionally ("attenuation is strong at high frequency," which the literature separately confirms qualitatively, e.g. the Saudi 73.5 GHz study).

**Conclusion: only the 14–22 GHz range is numerically trustworthy from this model.** Higher-frequency claims should be qualitative, not numeric, until a real high-frequency Saudi dataset is obtained.

## 2. Real events used as anchors (Part 1/9/10)

| ID | Date | Governorates | Corridor | Duration stated | Visibility | Wind | Source |
|---|---|---|---|---|---|---|---|
| A | 2025-05-19 | Jeddah, Rabigh, Bahra, Al-Kamil, Khulais | Highway 5 (Jeddah–Rabigh) | until 18:00 | near-total loss (qualitative) | NOT FOUND | NCM/SPA |
| B | 2024-07-24 | Bahra(Shuaiba), Al-Lith, Al-Qunfudhah | Highway 5 (south) | until 21:00 | near-total loss + elevated waves | NOT FOUND | NCM/SPA |
| C | 2025-07-10 | Jeddah | Highway 5 (Jeddah) | until 17:00 | "dust accumulation" (weaker language) | NOT FOUND | NCM/SPA |

**What is genuinely validated across all three:** that this exact type of event recurs repeatedly on the exact same real corridor, in the exact governorates named in the challenge. **What is NOT validated across all three:** any independent numeric attenuation or timing result — because onset time and wind speed were not found for any of them, the physics simulation itself is identical across all three (same assumed storm speed range), not three independently-computed results. Do not claim "validated across 3 events" beyond this scope.

## 3. Detection feasibility (computed, n=900 parameter combinations, full grid in `results/full_parameter_grid.csv`)

Detection rate (at 5 dB threshold) by **severity**:
- light: **30%** of tested combinations detected
- moderate: **70%**
- severe: **95%**

Detection rate by **frequency** (across all severities/spacings — note this partly reflects the extrapolation issue above, so treat >22 GHz rows with caution):
- 14 GHz: 33% · 18 GHz: 50% · 22 GHz: 58% · 40 GHz: 83%* · 73.5 GHz: 100%*
  (*inflated by the extrapolation breakdown noted in §1 — not to be quoted as a real detection-probability at these frequencies)

At **18 GHz, severe storm**, computed total attenuation by spacing:
- 2 km → 6.58 dB · 5 km → 16.46 dB · 10 km → 32.92 dB · 15 km → 49.38 dB
(all comfortably clear a 5 dB threshold — the physics of *detecting a severe storm* is not the weak point of this concept)

## 4. The 15-minute logging problem — quantified (Part 5/6/9, the headline finding of this round)

Across the full 900-row grid, the fraction of parameter combinations where the **true tower-detection order survives the logging interval intact** (`sequence_preserved`):

| Logging interval | % sequence preserved |
|---|---|
| 1 min | 100% |
| 5 min | 83% |
| 10 min | 58% |
| **15 min (industry-standard default)** | **50%** |
| 30 min | 17% |

By **spacing**: 2 km → 27% preserved · 5 km → 53% · 10 km → 80% · 15 km → 87%.

**Worked example (Event A anchor, 18 GHz, severe, 5 km spacing, 40 km/h storm, standard 15-min logging):**
True tower arrival times: 0, 7.5, 15, 22.5, 30 minutes.
**Observed (logged) times: 0, 15, 15, 30, 30 minutes** — towers 2&3 collapse onto the same logged timestamp, and so do towers 4&5. **`sequence_preserved = False`.** The system would see two simultaneous detections instead of a clear moving front, at this exact spacing/speed/logging combination — a directly demonstrated failure mode, not a hypothetical one. (See `figures/plot6_event_A_timeline.png`.)

## 5. Minimum viable real-world configuration (Part 13, derived from `results/spacing_speed_logging_table.csv`)

At the **standard industry 15-minute logging interval**, the system is only reliably **USEFUL** (not merely marginal) when:
- spacing ≥ **10 km** and storm speed ≤ **20 km/h**, or
- spacing ≥ **15 km** at storm speeds up to 20 km/h (marginal up to 40–60 km/h)

At **5 km spacing** (the tightest realistic hackathon-demo assumption) and a fast 40–60 km/h storm, standard 15-min logging is **USELESS** — confirmed by direct computation, not estimation. Useful operation at tight spacing (2–5 km) **requires 1–5 minute logging**, which per the CML-rainfall literature is achievable only through custom SNMP-polling arrangements (as done in the Czech Republic/Germany), not standard commercial NMS exports.

**Concrete target specification:** *"Point-to-point microwave backhaul, 14–22 GHz, ≥10 km inter-tower spacing (or ≥3 min custom-polled logging if spacing is tighter), minimum 3 spatially adjacent links, severe-storm detection only (light dust is not reliably detectable at any tested configuration)."*

## 6. Multi-link spatial confidence (Part 8)

An illustrative (not statistically validated — fault-rate is an assumed constant, see `results/multilink_confidence_illustrative.csv`) Bayesian-flavored calculation shows confidence-that-it's-dust-not-a-fault rising from a single affected link to 5 adjacent affected links. This demonstrates the **logic** is sound (more spatially coherent links = more confidence) but **is not a measured false-alarm rate** — no dataset exists to measure a real one. The wind-driven multi-link antenna misalignment risk (flagged in the prior round) is **not modeled here at all** — it remains a genuinely open, unquantified threat that this simulation cannot resolve without real link data.

## 7. Files
- `results/full_parameter_grid.csv`: 900-row grid (frequency x spacing x speed x severity x logging interval)
- `results/threshold_sensitivity.csv`: detectability at 2/5/10 dB thresholds
- `results/spacing_speed_logging_table.csv`: USEFUL/MARGINAL/USELESS verdicts (Nyquist-style heuristic, an assumption)
- `results/multilink_confidence_illustrative.csv`: illustrative only
- `data/events.csv`: three real NCM events, unknown fields marked NOT FOUND
- `figures/plot1` to `plot8`: attenuation vs distance and frequency, lead time vs spacing and speed, logging-interval effect, Event A timeline, schematic corridor, operating region

## 8. Caveat on source numbers
The Port Sudan, Haddad (1983) and Sabha figures were taken from abstracts and review summaries, not from full-text data tables. Verify them against the original papers before formal citation.
