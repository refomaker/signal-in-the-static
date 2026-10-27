"""
Generates all figures from results/. Run AFTER simulate.py:
    python src/plots.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from model import get_attenuation_per_km
from simulate import simulate_corridor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)

grid = pd.read_csv(os.path.join(RES, "full_parameter_grid.csv"))
sp = pd.read_csv(os.path.join(RES, "spacing_speed_logging_table.csv"))
plt.rcParams.update({"font.size": 10})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, name), dpi=140)
    plt.close(fig)


# 1 attenuation vs distance
fig, ax = plt.subplots(figsize=(6, 4.2))
d = np.linspace(0, 20, 100)
for f in [14, 18, 22]:
    ax.plot(d, get_attenuation_per_km(f, "severe")[0] * d, label=f"{f} GHz")
ax.axhline(5, color="gray", ls="--", lw=1, label="5 dB threshold (assumed)")
ax.set_xlabel("Link distance (km)"); ax.set_ylabel("Total attenuation (dB)")
ax.set_title("Attenuation vs. link distance - severe storm\n(14-22 GHz: literature-interpolated range)")
ax.legend(fontsize=8); save(fig, "plot1_attenuation_vs_distance.png")

# 2 attenuation vs frequency
fig, ax = plt.subplots(figsize=(6, 4.2))
fr = np.linspace(9.4, 40, 200)
for sv in ["light", "moderate", "severe"]:
    ax.plot(fr, [get_attenuation_per_km(f, sv)[0] for f in fr], label=sv)
ax.axvspan(9.4, 18, alpha=0.15, color="green", label="calibrated (2-pt fit)")
ax.axvspan(18, 40, alpha=0.15, color="red", label="extrapolated (low confidence)")
ax.set_yscale("log"); ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("Attenuation (dB/km)")
ax.set_title("Attenuation vs. frequency by severity\n(>18 GHz is extrapolation, not measurement)")
ax.legend(fontsize=8); save(fig, "plot2_attenuation_vs_frequency.png")

# 3 lead time vs spacing
fig, ax = plt.subplots(figsize=(6, 4.2))
for s in [20, 40, 60]:
    ax.plot([2, 5, 10, 15], [x / s * 60 for x in [2, 5, 10, 15]], marker="o", label=f"{s} km/h")
ax.set_xlabel("Tower spacing (km)"); ax.set_ylabel("True inter-tower travel time (min)")
ax.set_title("Warning lead-time potential vs. tower spacing\n(before sampling-interval losses)")
ax.legend(title="storm speed"); save(fig, "plot3_leadtime_vs_spacing.png")

# 4 lead time vs speed
fig, ax = plt.subplots(figsize=(6, 4.2))
for s in [2, 5, 10, 15]:
    ax.plot([20, 40, 60], [s / v * 60 for v in [20, 40, 60]], marker="o", label=f"{s} km spacing")
ax.set_xlabel("Storm speed (km/h)"); ax.set_ylabel("True inter-tower travel time (min)")
ax.set_title("Warning lead-time potential vs. storm speed"); ax.legend()
save(fig, "plot4_leadtime_vs_speed.png")

# 5 logging interval effect
fig, ax = plt.subplots(figsize=(6, 4.2))
seq = grid.groupby("logging_interval_min")["sequence_preserved"].mean() * 100
ax.bar(seq.index.astype(str), seq.values, color="#c0504d")
for i, v in enumerate(seq.values):
    ax.text(i, v + 1.5, f"{v:.0f}%", ha="center", fontsize=9)
ax.set_xlabel("Logging interval (minutes)")
ax.set_ylabel("% of combinations where tower\ndetection order is resolved")
ax.set_title("Effect of telecom NMS logging interval on\nspatial/temporal resolvability")
save(fig, "plot5_logging_interval_effect.png")

# 6 Event A timeline (SIMULATED, anchored to real Event A date/corridor)
r = simulate_corridor(18.0, "severe", 5, 5, 40, 15, 5.0)
fig, ax = plt.subplots(figsize=(7, 3.6))
tw = list(range(1, 6))
ax.scatter(r["true_times_min"], tw, color="green", label="True physical arrival (SIMULATED)", zorder=3)
ax.scatter(r["observed_times_min"], tw, color="red", marker="x", s=80,
           label="Observed @15-min logging (SIMULATED)", zorder=3)
for t, o, k in zip(r["true_times_min"], r["observed_times_min"], tw):
    ax.plot([t, o], [k, k], color="gray", ls=":", zorder=1)
ax.set_yticks(tw); ax.set_ylabel("Tower / link index (5 km spacing)")
ax.set_xlabel("Minutes since storm entered corridor (SIMULATED)")
ax.set_title("Event A (19 May 2025) replay: true vs. logged detection timing\n18 GHz, severe, 40 km/h, 15-min logging")
ax.legend(fontsize=8, loc="lower right"); save(fig, "plot6_event_A_timeline.png")

# 7 schematic corridor
fig, ax = plt.subplots(figsize=(8, 2.8))
ax.plot(np.linspace(0, 25, 500), np.zeros(500), color="black", lw=2, label="Corridor segment (schematic, 25 km)")
pos = [i * 5 for i in range(5)]
ax.scatter(pos, [0] * 5, color="blue", s=100, zorder=3, label="Simulated tower/link (SIMULATED position)")
for i, x in enumerate(pos):
    ax.annotate(f"T{i+1}\n{r['observed_times_min'][i]:.0f} min", (x, 0),
                textcoords="offset points", xytext=(0, 15), ha="center", fontsize=8)
ax.set_xlim(-4, 28); ax.set_ylim(-1.5, 1.5); ax.set_yticks([])
ax.set_xlabel("Distance along corridor (km) - SCHEMATIC, not real GPS coordinates")
ax.set_title("Schematic corridor with simulated detection times (no real tower locations are known)")
ax.legend(fontsize=7, loc="upper left"); save(fig, "plot7_schematic_corridor_map.png")

# 8 operating region at 15-min logging
sub = sp[sp.logging_interval_min == 15]
vm = {"USEFUL": 2, "MARGINAL": 1}
sps, sds = sorted(sub.spacing_km.unique()), sorted(sub.storm_speed_kmh.unique())
g = np.zeros((len(sps), len(sds)))
for i, s in enumerate(sps):
    for j, v in enumerate(sds):
        verdict = sub[(sub.spacing_km == s) & (sub.storm_speed_kmh == v)]["verdict"].iloc[0]
        g[i, j] = vm.get(verdict, 0)
fig, ax = plt.subplots(figsize=(6, 4.5))
ax.imshow(g, cmap=plt.cm.RdYlGn, vmin=0, vmax=2, aspect="auto")
ax.set_xticks(range(len(sds))); ax.set_xticklabels([f"{v} km/h" for v in sds])
ax.set_yticks(range(len(sps))); ax.set_yticklabels([f"{s} km" for s in sps])
for i in range(len(sps)):
    for j in range(len(sds)):
        ax.text(j, i, ["USELESS", "MARGINAL", "USEFUL"][int(g[i, j])], ha="center", va="center", fontsize=8)
ax.set_xlabel("Storm speed"); ax.set_ylabel("Tower spacing")
ax.set_title("Operating region at STANDARD 15-min telecom logging")
save(fig, "plot8_operating_region.png")
print("Figures written to figures/")
