"""
Signal in the Static - simulation engine.
Run from the repo root:  python src/simulate.py
Writes CSVs to results/ and data/.
"""
import os
import numpy as np
import pandas as pd
from model import get_attenuation_per_km

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
DATA = os.path.join(ROOT, "data")

# REAL events: NCM public bulletins as reported by Saudi Press Agency (SPA).
# Any field not stated in the bulletin is "NOT FOUND" -- never invented.
EVENTS = [
    {"id": "A", "date": "2025-05-19",
     "governorates": "Jeddah, Rabigh, Bahra, Al-Kamil, Khulais",
     "corridor": "Highway 5 (Jeddah-Rabigh section)",
     "start": "NOT FOUND", "end": "18:00 local (stated in bulletin)",
     "visibility": "qualitative: near-total loss of horizontal visibility",
     "wind_speed": "NOT FOUND", "wind_direction": "NOT FOUND",
     "severity_label": "severe (qualitative, per NCM wording)",
     "source": "NCM via SPA, 19 May 2025"},
    {"id": "B", "date": "2024-07-24",
     "governorates": "Bahra (Shuaiba), Al-Lith, Al-Qunfudhah",
     "corridor": "Highway 5 (southern coastal section)",
     "start": "NOT FOUND", "end": "21:00 local (stated in bulletin)",
     "visibility": "qualitative: near-total loss; elevated wave height also noted",
     "wind_speed": "NOT FOUND", "wind_direction": "NOT FOUND",
     "severity_label": "severe (qualitative, per NCM wording)",
     "source": "NCM via SPA, 24 July 2024"},
    {"id": "C", "date": "2025-07-10",
     "governorates": "Jeddah",
     "corridor": "Highway 5 (Jeddah section)",
     "start": "NOT FOUND", "end": "17:00 local (stated in bulletin)",
     "visibility": "qualitative: dust accumulation, weaker wording than A/B",
     "wind_speed": "NOT FOUND", "wind_direction": "NOT FOUND",
     "severity_label": "moderate (qualitative, per NCM wording)",
     "source": "NCM via SPA, 10 July 2025"},
]


def simulate_corridor(freq_ghz, severity, spacing_km, n_links, storm_speed_kmh,
                      logging_interval_min, threshold_db, start_offset_km=0.0):
    """Storm front moving along a straight corridor of n_links hops.
    Hop path length = tower spacing (ENGINEERING ASSUMPTION).
    Observed time = next logging tick at/after true arrival (worst case)."""
    per_km, label = get_attenuation_per_km(freq_ghz, severity)
    total_att = per_km * spacing_km
    detected = total_att >= threshold_db

    true_min = np.array([(start_offset_km + i * spacing_km) / storm_speed_kmh * 60.0
                         for i in range(n_links)])
    obs_min = np.ceil(true_min / logging_interval_min) * logging_interval_min

    order_true = np.argsort(true_min)
    order_obs = np.argsort(obs_min, kind="stable")
    seq_ok = bool(np.array_equal(order_true, order_obs) and len(set(obs_min)) == n_links)

    return {
        "freq_ghz": freq_ghz, "severity": severity, "spacing_km": spacing_km,
        "n_links": n_links, "storm_speed_kmh": storm_speed_kmh,
        "logging_interval_min": logging_interval_min, "threshold_db": threshold_db,
        "atten_per_km_db": per_km, "atten_label": label,
        "total_att_db_per_link": total_att, "detected": bool(detected),
        "true_inter_tower_min": spacing_km / storm_speed_kmh * 60.0,
        "mean_sampling_loss_min": float(np.mean(obs_min - true_min)),
        "sequence_preserved": seq_ok,
        "true_times_min": true_min.tolist(), "observed_times_min": obs_min.tolist(),
    }


def main():
    os.makedirs(RESULTS, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)
    pd.DataFrame(EVENTS).to_csv(os.path.join(DATA, "events.csv"), index=False)

    freqs = [14, 18, 22, 40, 73.5]
    spacings = [2, 5, 10, 15]
    speeds = [20, 40, 60]
    sevs = ["light", "moderate", "severe"]
    logs = [1, 5, 10, 15, 30]

    rows = [simulate_corridor(f, sv, sp, 5, sd, li, 5.0)
            for f in freqs for sp in spacings for sd in speeds for sv in sevs for li in logs]
    pd.DataFrame(rows).to_csv(os.path.join(RESULTS, "full_parameter_grid.csv"), index=False)

    thr = []
    for f in freqs:
        for sv in sevs:
            per_km, label = get_attenuation_per_km(f, sv)
            for sp in spacings:
                for t in [2, 5, 10]:
                    thr.append({"freq_ghz": f, "severity": sv, "spacing_km": sp,
                                "atten_per_km_db": per_km, "total_att_db": per_km * sp,
                                "threshold_db": t, "detected": per_km * sp >= t, "label": label})
    pd.DataFrame(thr).to_csv(os.path.join(RESULTS, "threshold_sensitivity.csv"), index=False)

    srows = []
    for sp in spacings:
        for sd in speeds:
            inter = sp / sd * 60.0
            for li in logs:
                # Nyquist-style heuristic (ASSUMPTION, not a cited standard)
                if li <= inter / 2:
                    v = "USEFUL"
                elif li <= inter:
                    v = "MARGINAL"
                else:
                    v = "USELESS (storm likely passes between samples)"
                srows.append({"spacing_km": sp, "storm_speed_kmh": sd,
                              "true_inter_tower_time_min": round(inter, 2),
                              "logging_interval_min": li, "verdict": v})
    pd.DataFrame(srows).to_csv(os.path.join(RESULTS, "spacing_speed_logging_table.csv"), index=False)

    mrows = []
    for n in [1, 2, 3, 5]:
        p_fault = 0.15  # ASSUMED, illustrative only
        mrows.append({"n_adjacent_links_affected": n,
                      "illustrative_confidence_dust_not_fault": round(1 - p_fault ** n, 4),
                      "note": "ILLUSTRATIVE ONLY - fault rate 0.15 is an assumption, not measured"})
    pd.DataFrame(mrows).to_csv(os.path.join(RESULTS, "multilink_confidence_illustrative.csv"), index=False)
    print("Simulation complete: results/ and data/ written.")


if __name__ == "__main__":
    main()
