"""
Signal in the Static - physical attenuation model
=================================================
Provenance labels used throughout:
  REAL_OBS      a number taken directly from a cited field measurement
  DERIVED       arithmetic performed on a REAL_OBS value
  ASSUMPTION    an engineering choice not directly measured in any cited source
  EXTRAPOLATION a value obtained by extending a fit beyond its calibration range

IMPORTANT: no single field study sweeps 14-73.5 GHz on one storm. We stitch together
two separate papers (different storms, different severities). The fit below is a
2-point power law and is only numerically trustworthy between ~9.4 and ~22 GHz.
"""
import numpy as np

# Literature anchors (REAL_OBS), as cited in review/field papers:
#  - Haddad (1983): 9.4 GHz, 0.3 dB/km dry, 0.8 dB/km at 10% particle moisture
#  - Sabha, Libya (Ku-band ~14 GHz, 60% RH): 0.13 - 9.78 dB/km across measured range
#  - Port Sudan: >16 dB over a 4.86 km link at 18 GHz, severe storm (visibility < 50 m)
PORT_SUDAN_TOTAL_DB = 16.0
PORT_SUDAN_LINK_KM = 4.86
PORT_SUDAN_DB_PER_KM = PORT_SUDAN_TOTAL_DB / PORT_SUDAN_LINK_KM   # DERIVED = 3.292 dB/km

F1, A1 = 9.4, 0.8                       # REAL_OBS (Haddad, wet/severe)
F2, A2 = 18.0, 3.292                    # REAL_OBS/DERIVED (Port Sudan, severe; 16/4.86 rounded to 3 d.p.)

N_EXPONENT = np.log(A2 / A1) / np.log(F2 / F1)   # DERIVED power-law exponent (~2.177)


def severe_attenuation_db_per_km(freq_ghz):
    """Severe-storm dB/km: A(f) = A2 * (f/F2)^n.
    Returns (value, label). Outside 9.4-18 GHz it is an EXTRAPOLATION and, above
    ~22 GHz, physically implausible (e.g. ~70 dB/km at 73.5 GHz)."""
    value = A2 * (freq_ghz / F2) ** N_EXPONENT
    if F1 <= freq_ghz <= F2:
        label = "INTERPOLATION (2-point power-law fit across Haddad 9.4GHz and Port Sudan 18GHz)"
    else:
        label = "EXTRAPOLATION (outside the 9.4-18 GHz calibration range -- low confidence)"
    return value, label


def moderate_attenuation_db_per_km(freq_ghz):
    """ASSUMPTION: moderate = 25% of severe. The Sabha (~1%) and Haddad (~37%) dry/wet
    ratios disagree by an order of magnitude, so no single scaling factor is well
    supported by the literature."""
    return severe_attenuation_db_per_km(freq_ghz)[0] * 0.25


def light_attenuation_db_per_km(freq_ghz):
    """ASSUMPTION: light = 5% of severe (order of magnitude anchored to Sabha low end)."""
    return severe_attenuation_db_per_km(freq_ghz)[0] * 0.05


def get_attenuation_per_km(freq_ghz, severity):
    if severity == "severe":
        return severe_attenuation_db_per_km(freq_ghz)
    fn = {"light": light_attenuation_db_per_km, "moderate": moderate_attenuation_db_per_km}[severity]
    base_label = severe_attenuation_db_per_km(freq_ghz)[1]
    return fn(freq_ghz), f"ASSUMPTION (scaled from severe-storm {base_label})"


if __name__ == "__main__":
    print(f"Fitted exponent n = {N_EXPONENT:.3f}")
    for f in [9.4, 14, 18, 22, 40, 73.5]:
        print(f, [round(get_attenuation_per_km(f, s)[0], 3) for s in ("light", "moderate", "severe")])
