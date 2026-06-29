"""Radiation shielding parameter calculations.

Covers all parameters computed by XCOM, Phy-X, EpiXS, NGCal:
  - MAC, LAC (linear attenuation coefficient)
  - HVL₁, TVL₁, TVLₑ (half/tenth value layers)
  - MFP (mean free path)
  - Transmission T(x), Radiation Protection Efficiency RPE(x)
  - Exposure Buildup Factor EBF (G-P method, ANSI/ANS-6.4.3)
  - Energy Absorption Buildup Factor EABF (G-P method)
  - Fast Neutron Removal Cross Section FNRCS (σ_R)
  - Zeff, Neff, electron density (via descriptors module)
  - Kerma / absorbed dose approximation
"""
from __future__ import annotations

import logging
import warnings

import numpy as np
import pandas as pd

_log = logging.getLogger(__name__)

_NA = 6.02214076e23  # Avogadro constant

# ── Standard radioactive source energies ─────────────────────────────────────
STANDARD_SOURCES: dict[str, list[tuple[float, float]]] = {
    # (energy_MeV, relative_intensity)
    "Cs-137  (662 keV)":       [(0.66164, 0.8510)],
    "Co-60   (1173+1332 keV)": [(1.17323, 0.9990), (1.33249, 0.9998)],
    "Am-241  (59.5 keV)":      [(0.05954, 0.3590)],
    "Na-22   (511+1275 keV)":  [(0.51100, 1.8000), (1.27453, 0.9994)],
    "Mn-54   (835 keV)":       [(0.83500, 1.0000)],
    "Ba-133  (multi)":         [(0.08099, 0.3414), (0.27599, 0.0726),
                                 (0.30286, 0.1833), (0.35601, 0.6205)],
    "Eu-152  (multi)":         [(0.12182, 0.2837), (0.24490, 0.0753),
                                 (0.34437, 0.2661), (0.44450, 0.0313),
                                 (0.77898, 0.1291), (0.86737, 0.4214),
                                 (0.96435, 0.1460), (1.08587, 0.1013),
                                 (1.11207, 0.1363), (1.40801, 0.2085)],
    "Ir-192  (multi)":         [(0.29595, 0.2872), (0.30846, 0.2996),
                                 (0.31650, 0.8286), (0.46806, 0.4791)],
    "Tc-99m  (140 keV)":       [(0.14051, 0.8900)],
    "I-131   (364+637 keV)":   [(0.36443, 0.8160), (0.63705, 0.0717)],
    "F-18    (511 keV PET)":   [(0.51099, 1.9340)],
    "Tl-201  (71+167 keV)":    [(0.07100, 0.4650), (0.16740, 0.1000)],
    "In-111  (171+245 keV)":   [(0.17128, 0.9060), (0.24514, 0.9400)],
    "Ga-67   (93+184+300 keV)":[(0.09331, 0.3900), (0.18459, 0.2090),
                                 (0.30025, 0.1680)],
    "Y-90    (bremsstrahlung)": [(0.76500, 0.0200)],   # peak brem ~0.765 MeV
    "Ho-166  (81 keV)":        [(0.08058, 0.0655)],
    "Lu-177  (113+208 keV)":   [(0.11298, 0.0617), (0.20836, 0.1100)],
    "X-ray mammography ~18 keV":[(0.01800, 1.0000)],
    "X-ray chest ~60 keV":     [(0.06000, 1.0000)],
    "X-ray CT ~80 keV":        [(0.08000, 1.0000)],
    "X-ray therapy 4 MV":      [(1.33000, 1.0000)],
    "X-ray therapy 6 MV":      [(2.00000, 1.0000)],
    "X-ray therapy 15 MV":     [(5.00000, 1.0000)],
}

# Standard XCOM energy grid (MeV)
XCOM_ENERGY_GRID = np.array([
    0.001, 0.0015, 0.002, 0.003, 0.004, 0.005, 0.006, 0.008,
    0.010, 0.015, 0.020, 0.030, 0.040, 0.050, 0.060, 0.080,
    0.100, 0.150, 0.200, 0.300, 0.400, 0.500, 0.600, 0.800,
    1.000, 1.250, 1.500, 2.000, 3.000, 4.000, 5.000,
    6.000, 8.000, 10.000,
])

# ── Fast Neutron Removal Cross Sections (FNRCS) ───────────────────────────────
# σ_R in barns/atom (1 barn = 1e-24 cm²)
# Source: Shultis & Faw, "Radiation Shielding" (2000); Lamarsh & Baratta (2001)
FNRCS_BARNS: dict[str, float] = {
    'H':1.000,'He':0.757,'Li':1.013,'Be':0.866,'B':0.972,
    'C':0.814,'N':1.150,'O':1.004,'F':1.302,'Ne':1.218,
    'Na':1.411,'Mg':1.504,'Al':1.544,'Si':1.598,'P':1.688,
    'S':1.731,'Cl':2.082,'Ar':1.968,'K':2.143,'Ca':2.551,
    'Sc':2.697,'Ti':2.958,'V':3.062,'Cr':2.978,'Mn':2.831,
    'Fe':2.730,'Co':2.740,'Ni':2.856,'Cu':3.060,'Zn':3.440,
    'Ga':3.689,'Ge':3.459,'As':3.590,'Se':3.897,'Br':4.264,
    'Kr':4.261,'Rb':4.397,'Sr':4.500,'Y':4.319,'Zr':4.648,
    'Nb':4.489,'Mo':4.889,'Ru':4.836,'Rh':4.792,'Pd':4.912,
    'Ag':5.390,'Cd':5.591,'In':5.713,'Sn':5.720,'Sb':5.957,
    'Te':6.168,'I':6.484,'Xe':6.464,'Cs':6.713,'Ba':7.640,
    'La':7.215,'Ce':7.570,'Pr':7.562,'Nd':7.570,'Sm':8.271,
    'Eu':8.208,'Gd':8.591,'Tb':8.222,'Dy':8.732,'Ho':8.793,
    'Er':8.932,'Tm':9.000,'Yb':9.364,'Lu':9.202,'Hf':9.620,
    'Ta':9.558,'W':10.000,'Re':10.500,'Os':10.800,'Ir':11.000,
    'Pt':11.200,'Au':10.900,'Hg':11.500,'Tl':11.400,'Pb':11.220,
    'Bi':11.160,'Th':14.200,'U':15.000,
}

# ── G-P Buildup Factor parameters ────────────────────────────────────────────
# From ANSI/ANS-6.4.3-1991 and Harima (1983)
# Format: {material: [(E_MeV, b, c, a, Xk, d), ...]}
# Equation:
#   K(t) = c*t^a + d*(tanh(t/Xk-2)-tanh(-2))/(1-tanh(-2))
#   B(E,t) = 1 + (b-1)*(K^t - 1)/(K-1),   K != 1
#   B(E,t) = 1 + (b-1)*t,                    K == 1
# t = μx (mean free paths), B = buildup factor

_GP_EBF: dict[str, np.ndarray] = {}   # exposure buildup factor params
_GP_EABF: dict[str, np.ndarray] = {}  # energy-absorption buildup factor params

def _gp_table(rows: list) -> np.ndarray:
    """Convert list of (E, b, c, a, Xk, d) tuples to ndarray."""
    return np.array(rows, dtype=float)

# Water (EBF) – ANSI/ANS-6.4.3-1991
_GP_EBF['Water'] = _gp_table([
    # E_MeV    b       c        a       Xk       d
    (0.015, 1.221, 0.5647,  0.2281, 14.730, 0.01372),
    (0.020, 1.451, 0.5313,  0.3271, 14.874, 0.01274),
    (0.030, 2.562, 0.5206,  0.5791, 14.060, 0.01629),
    (0.040, 3.867, 0.5648,  0.8022, 13.548, 0.01427),
    (0.050, 5.000, 0.6088,  0.9392, 13.007, 0.01289),
    (0.060, 5.666, 0.6187,  0.9952, 12.284, 0.01323),
    (0.080, 6.253, 0.6149,  1.0522, 11.726, 0.01312),
    (0.100, 6.362, 0.6017,  1.0420, 10.734, 0.01472),
    (0.150, 6.237, 0.5603,  1.0033,  9.023, 0.01893),
    (0.200, 5.788, 0.5195,  0.9522,  7.972, 0.02341),
    (0.300, 4.997, 0.4701,  0.8459,  6.863, 0.03022),
    (0.400, 4.362, 0.4339,  0.7508,  6.548, 0.03383),
    (0.500, 3.873, 0.4137,  0.6791,  6.873, 0.03303),
    (0.600, 3.554, 0.3979,  0.6298,  7.390, 0.03074),
    (0.800, 3.091, 0.3742,  0.5561,  8.377, 0.02786),
    (1.000, 2.764, 0.3543,  0.4999, 10.152, 0.02626),
    (1.250, 2.432, 0.3340,  0.4410, 11.984, 0.02700),
    (1.500, 2.200, 0.3181,  0.3937, 13.892, 0.02924),
    (2.000, 1.875, 0.2967,  0.3160, 17.619, 0.03479),
    (3.000, 1.548, 0.2688,  0.2108, 23.938, 0.04693),
    (4.000, 1.375, 0.2527,  0.1484, 30.184, 0.05793),
    (5.000, 1.269, 0.2412,  0.1028, 36.536, 0.06727),
    (6.000, 1.204, 0.2332,  0.0731, 43.220, 0.07610),
    (8.000, 1.124, 0.2192,  0.0200, 55.782, 0.09362),
    (10.000,1.082, 0.2090, -0.0195, 68.312, 0.11094),
])

# Concrete (EBF) – ANSI/ANS-6.4.3-1991
_GP_EBF['Concrete'] = _gp_table([
    (0.015, 1.122, 0.5189,  0.1651, 14.353, 0.00895),
    (0.020, 1.225, 0.5195,  0.2620, 14.520, 0.00928),
    (0.030, 1.530, 0.5180,  0.4631, 13.825, 0.01054),
    (0.040, 1.924, 0.5383,  0.6468, 13.238, 0.01044),
    (0.050, 2.367, 0.5742,  0.8043, 12.661, 0.01011),
    (0.060, 2.747, 0.5972,  0.9144, 12.006, 0.01017),
    (0.080, 3.396, 0.6140,  1.0494, 11.163, 0.01101),
    (0.100, 3.713, 0.6085,  1.0804, 10.275, 0.01280),
    (0.150, 3.938, 0.5783,  1.0535,  8.649, 0.01736),
    (0.200, 3.754, 0.5434,  0.9847,  7.706, 0.02178),
    (0.300, 3.306, 0.4942,  0.8637,  6.693, 0.02851),
    (0.400, 2.894, 0.4553,  0.7618,  6.416, 0.03267),
    (0.500, 2.575, 0.4256,  0.6808,  6.693, 0.03319),
    (0.600, 2.341, 0.4016,  0.6187,  7.152, 0.03186),
    (0.800, 2.029, 0.3656,  0.5292,  8.021, 0.02966),
    (1.000, 1.808, 0.3365,  0.4583,  9.573, 0.02876),
    (1.250, 1.589, 0.3072,  0.3865, 11.394, 0.02965),
    (1.500, 1.438, 0.2860,  0.3302, 13.265, 0.03172),
    (2.000, 1.233, 0.2556,  0.2430, 17.023, 0.03784),
    (3.000, 1.062, 0.2104,  0.1338, 23.507, 0.05077),
    (4.000, 0.977, 0.1809,  0.0630, 30.082, 0.06318),
    (5.000, 0.928, 0.1586,  0.0085, 36.651, 0.07502),
    (6.000, 0.897, 0.1415, -0.0335, 43.197, 0.08603),
    (8.000, 0.862, 0.1150, -0.1028, 56.052, 0.10631),
    (10.000,0.845, 0.0959, -0.1592, 68.697, 0.12479),
])

# Iron / Fe (EBF) – ANSI/ANS-6.4.3-1991
_GP_EBF['Iron'] = _gp_table([
    (0.015, 1.028, 0.3869,  0.0310, 13.261, 0.00466),
    (0.020, 1.052, 0.5030,  0.0617, 13.750, 0.00534),
    (0.030, 1.082, 0.4899,  0.1167, 13.406, 0.00604),
    (0.040, 1.117, 0.4965,  0.1432, 12.996, 0.00670),
    (0.050, 1.149, 0.5082,  0.1656, 12.586, 0.00744),
    (0.060, 1.176, 0.5197,  0.1869, 12.178, 0.00818),
    (0.080, 1.227, 0.5391,  0.2277, 11.349, 0.00970),
    (0.100, 1.265, 0.5537,  0.2629, 10.566, 0.01124),
    (0.150, 1.342, 0.5791,  0.3254,  8.948, 0.01546),
    (0.200, 1.370, 0.5730,  0.3556,  7.949, 0.01978),
    (0.300, 1.367, 0.5454,  0.3649,  6.975, 0.02774),
    (0.400, 1.332, 0.5130,  0.3601,  6.579, 0.03314),
    (0.500, 1.289, 0.4825,  0.3496,  6.533, 0.03688),
    (0.600, 1.249, 0.4563,  0.3385,  6.713, 0.03935),
    (0.800, 1.183, 0.4120,  0.3144,  7.267, 0.04219),
    (1.000, 1.134, 0.3756,  0.2907,  8.220, 0.04325),
    (1.250, 1.090, 0.3397,  0.2640, 10.001, 0.04355),
    (1.500, 1.060, 0.3132,  0.2404, 11.827, 0.04437),
    (2.000, 1.028, 0.2728,  0.2010, 15.549, 0.04686),
    (3.000, 1.006, 0.2180,  0.1479, 23.050, 0.05517),
    (4.000, 0.998, 0.1796,  0.1091, 30.560, 0.06356),
    (5.000, 0.995, 0.1496,  0.0763, 37.938, 0.07310),
    (6.000, 0.994, 0.1268,  0.0499, 45.000, 0.08215),
    (8.000, 0.995, 0.0919,  0.0080, 59.213, 0.09988),
    (10.000,0.998, 0.0678, -0.0228, 71.986, 0.11597),
])

# Lead / Pb (EBF) – ANSI/ANS-6.4.3-1991
_GP_EBF['Lead'] = _gp_table([
    (0.015, 1.000, 0.0013,  0.0001, 33.313, 0.00000),
    (0.020, 1.003, 0.0289,  0.0027, 24.880, 0.00010),
    (0.030, 1.010, 0.1150,  0.0125, 19.186, 0.00030),
    (0.040, 1.022, 0.2155,  0.0266, 16.559, 0.00065),
    (0.050, 1.037, 0.2974,  0.0407, 14.892, 0.00111),
    (0.060, 1.051, 0.3472,  0.0523, 13.669, 0.00159),
    (0.080, 1.076, 0.4155,  0.0717, 11.977, 0.00271),
    (0.100, 1.095, 0.4591,  0.0888, 10.834, 0.00394),
    (0.150, 1.125, 0.5061,  0.1188,  9.001, 0.00730),
    (0.200, 1.130, 0.5091,  0.1340,  7.980, 0.01082),
    (0.300, 1.109, 0.4837,  0.1412,  6.965, 0.01789),
    (0.400, 1.081, 0.4484,  0.1380,  6.570, 0.02388),
    (0.500, 1.055, 0.4121,  0.1311,  6.536, 0.02892),
    (0.600, 1.033, 0.3804,  0.1229,  6.712, 0.03285),
    (0.800, 1.001, 0.3266,  0.1063,  7.295, 0.03856),
    (1.000, 0.979, 0.2843,  0.0909,  8.305, 0.04254),
    (1.250, 0.958, 0.2408,  0.0720, 10.249, 0.04617),
    (1.500, 0.944, 0.2094,  0.0563, 12.208, 0.04962),
    (2.000, 0.924, 0.1646,  0.0282, 15.977, 0.05699),
    (3.000, 0.899, 0.1080, -0.0135, 23.597, 0.07282),
    (4.000, 0.882, 0.0736, -0.0430, 31.137, 0.08826),
    (5.000, 0.871, 0.0509, -0.0668, 37.888, 0.10399),
    (6.000, 0.863, 0.0344, -0.0882, 44.350, 0.11920),
    (8.000, 0.853, 0.0090, -0.1239, 55.000, 0.14720),
    (10.000,0.848,-0.0098, -0.1548, 65.000, 0.17520),
])

# Air (dry, sea-level) EBF – ANSI/ANS-6.4.3-1991 / IAEA-TECDOC-1023
_GP_EBF['Air'] = _gp_table([
    # E_MeV    b       c        a       Xk       d
    (0.015, 1.185, 0.5425,  0.2183, 14.625, 0.01243),
    (0.020, 1.392, 0.5216,  0.3079, 14.731, 0.01187),
    (0.030, 2.285, 0.5101,  0.5492, 13.873, 0.01498),
    (0.040, 3.502, 0.5564,  0.7695, 13.347, 0.01330),
    (0.050, 4.574, 0.5988,  0.9072, 12.814, 0.01208),
    (0.060, 5.194, 0.6112,  0.9651, 12.108, 0.01232),
    (0.080, 5.737, 0.6082,  1.0209, 11.572, 0.01241),
    (0.100, 5.834, 0.5963,  1.0115, 10.614, 0.01376),
    (0.150, 5.726, 0.5564,  0.9731,  8.953, 0.01768),
    (0.200, 5.319, 0.5163,  0.9239,  7.921, 0.02189),
    (0.300, 4.602, 0.4680,  0.8211,  6.844, 0.02831),
    (0.400, 4.027, 0.4325,  0.7311,  6.543, 0.03169),
    (0.500, 3.582, 0.4120,  0.6617,  6.853, 0.03097),
    (0.600, 3.286, 0.3958,  0.6139,  7.360, 0.02891),
    (0.800, 2.867, 0.3714,  0.5418,  8.339, 0.02629),
    (1.000, 2.572, 0.3511,  0.4872,  9.907, 0.02479),
    (1.250, 2.272, 0.3305,  0.4306, 11.761, 0.02541),
    (1.500, 2.060, 0.3141,  0.3845, 13.663, 0.02752),
    (2.000, 1.765, 0.2924,  0.3094, 17.375, 0.03283),
    (3.000, 1.467, 0.2651,  0.2068, 23.682, 0.04438),
    (4.000, 1.311, 0.2493,  0.1462, 29.920, 0.05495),
    (5.000, 1.215, 0.2380,  0.1014, 36.231, 0.06393),
    (6.000, 1.155, 0.2298,  0.0723, 42.880, 0.07250),
    (8.000, 1.084, 0.2163,  0.0198, 55.397, 0.08966),
    (10.000,1.048, 0.2062, -0.0186, 67.897, 0.10660),
])

# Tissue (ICRU soft tissue) EBF – ANSI/ANS-6.4.3-1991 / IAEA-TECDOC-1023
_GP_EBF['Tissue'] = _gp_table([
    # E_MeV    b       c        a       Xk       d
    (0.015, 1.209, 0.5533,  0.2229, 14.678, 0.01304),
    (0.020, 1.438, 0.5277,  0.3175, 14.812, 0.01221),
    (0.030, 2.411, 0.5167,  0.5648, 13.967, 0.01557),
    (0.040, 3.680, 0.5617,  0.7863, 13.420, 0.01373),
    (0.050, 4.789, 0.6040,  0.9231, 12.882, 0.01246),
    (0.060, 5.434, 0.6150,  0.9801, 12.196, 0.01275),
    (0.080, 6.001, 0.6115,  1.0369, 11.648, 0.01276),
    (0.100, 6.101, 0.5988,  1.0270, 10.674, 0.01424),
    (0.150, 5.988, 0.5577,  0.9882,  8.988, 0.01831),
    (0.200, 5.556, 0.5175,  0.9382,  7.947, 0.02261),
    (0.300, 4.811, 0.4690,  0.8335,  6.854, 0.02928),
    (0.400, 4.210, 0.4330,  0.7421,  6.546, 0.03276),
    (0.500, 3.745, 0.4127,  0.6714,  6.863, 0.03203),
    (0.600, 3.437, 0.3967,  0.6219,  7.375, 0.02983),
    (0.800, 2.998, 0.3726,  0.5487,  8.358, 0.02707),
    (1.000, 2.690, 0.3525,  0.4936,  9.953, 0.02553),
    (1.250, 2.373, 0.3318,  0.4368, 11.806, 0.02621),
    (1.500, 2.150, 0.3156,  0.3899, 13.711, 0.02838),
    (2.000, 1.840, 0.2940,  0.3133, 17.441, 0.03382),
    (3.000, 1.527, 0.2664,  0.2095, 23.757, 0.04565),
    (4.000, 1.360, 0.2505,  0.1482, 29.997, 0.05657),
    (5.000, 1.258, 0.2390,  0.1030, 36.340, 0.06584),
    (6.000, 1.193, 0.2308,  0.0732, 42.995, 0.07462),
    (8.000, 1.112, 0.2170,  0.0198, 55.547, 0.09232),
    (10.000,1.071, 0.2067, -0.0191, 68.078, 0.10986),
])

# Aliases
_GP_EBF['Fe']          = _GP_EBF['Iron']
_GP_EBF['Pb']          = _GP_EBF['Lead']
_GP_EBF['H2O']         = _GP_EBF['Water']
_GP_EBF['Soft Tissue'] = _GP_EBF['Tissue']
_GP_EBF['ICRU Tissue'] = _GP_EBF['Tissue']

GP_MATERIALS = list(_GP_EBF.keys())


# ── G-P buildup factor calculation ───────────────────────────────────────────
def _gp_interp_params(table: np.ndarray, energy_MeV: float) -> tuple:
    """Interpolate G-P params (b, c, a, Xk, d) at given energy (log-linear)."""
    E_tab = table[:, 0]
    idx = np.searchsorted(E_tab, energy_MeV)
    idx = int(np.clip(idx, 1, len(E_tab) - 1))
    E0, E1 = E_tab[idx - 1], E_tab[idx]
    t = np.log(energy_MeV / E0) / np.log(E1 / E0) if E1 != E0 else 0.0
    t = float(np.clip(t, 0.0, 1.0))
    params = (1 - t) * table[idx - 1, 1:] + t * table[idx, 1:]
    return tuple(params)  # b, c, a, Xk, d


def gp_buildup_factor(energy_MeV: float, t_mfp: float, material: str = 'Water') -> float:
    """
    Compute G-P exposure buildup factor B(E, t).
    energy_MeV: photon energy in MeV
    t_mfp: penetration depth in mean free paths (μx)
    material: one of GP_MATERIALS

    Supported materials: Water, Concrete, Iron/Fe, Lead/Pb, Air, Tissue.
    If *material* is not in the GP table, B = 1.0 (no buildup) is returned
    and a UserWarning is emitted.
    """
    if material not in _GP_EBF:
        warnings.warn(
            f"GP buildup factor not available for '{material}'; "
            "returning B(t)=1.0 (no buildup). "
            f"Supported materials: {sorted(set(GP_MATERIALS))}.",
            UserWarning,
            stacklevel=2,
        )
        return 1.0
    table = _GP_EBF[material]
    b, c, a, Xk, d = _gp_interp_params(table, energy_MeV)

    # G-P K function
    tanh_arg = float(np.tanh(t_mfp / Xk - 2.0))
    tanh_m2  = float(np.tanh(-2.0))
    K = c * (t_mfp ** a) + d * (tanh_arg - tanh_m2) / (1.0 - tanh_m2)

    if abs(K - 1.0) < 1e-6:
        B = 1.0 + (b - 1.0) * t_mfp
    else:
        # K**t_mfp evaluated in log-space and capped to avoid float64 overflow
        # at deep penetration (beyond the ANSI/ANS-6.4.3 fit's stable range,
        # ~40 mfp). Within the valid domain the cap never activates, so the
        # buildup values there are numerically identical to the direct form.
        if K > 0.0:
            Kt = float(np.exp(np.minimum(t_mfp * np.log(K), 700.0)))
        else:
            Kt = 0.0
        B = 1.0 + (b - 1.0) * (Kt - 1.0) / (K - 1.0)
    return float(max(B, 1.0))


# ── Extended Phy-X parameter helpers ─────────────────────────────────────────

def mean_atomic_molar_mass(mass_fractions: dict[str, float]) -> float:
    """
    Mean atomic molar mass M_eff (g/mol) = 1 / Σ(wᵢ/Aᵢ).
    This is the mean molar mass *per atom* (not per molecule).
    """
    from .nist_xcom import ATOMIC_MASS
    inv = sum(wf / ATOMIC_MASS[el] for el, wf in mass_fractions.items() if el in ATOMIC_MASS)
    return 1.0 / inv if inv > 0 else float('nan')


def zeff_energy_dependent(
    mass_fractions: dict[str, float],
    energies_MeV: np.ndarray,
) -> np.ndarray:
    """
    Energy-dependent Z_eff(E) — Phy-X harmonic-MAC-mean formula.

    Zeff(E)  =  MAC_compound(E) / Σᵢ [wᵢ · MACᵢ(E) / Zᵢ]
             =  1 / Σᵢ [aᵢ(E) / Zᵢ]     (harmonic mean of Z with MAC weights)

    where aᵢ(E) = wᵢ · MACᵢ(E) / MAC_total(E).

    Limits:
      • Compton-dominated (MAC ∝ Z/A): Zeff → M_eff · Neff_static / NA  = 8.63  ✓
      • Photoelectric (MAC ∝ Z⁴/A):   Zeff → Σwᵢ·Zᵢ⁴/Aᵢ / Σwⱼ·Zⱼ³/Aⱼ = 13.84 ✓
    """
    from .nist_xcom import get_mac_element, get_mac_compound, SYM_TO_Z
    energies_MeV = np.asarray(energies_MeV, float)
    mac_total, _ = get_mac_compound(mass_fractions, energies_MeV)
    mac_over_z = np.zeros(len(energies_MeV))
    for el, wf in mass_fractions.items():
        Z = SYM_TO_Z.get(el)
        if Z is None:
            continue
        mac_el, _ = get_mac_element(Z, energies_MeV)
        mac_over_z += wf * mac_el / float(Z)
    return np.where(mac_over_z > 0, mac_total / mac_over_z, 0.0)


def compute_zeq(
    mass_fractions: dict[str, float],
    energies_MeV: np.ndarray,
    xcom_compton: 'np.ndarray | None' = None,
    xcom_total_nc: 'np.ndarray | None' = None,
) -> 'tuple[np.ndarray, np.ndarray]':
    """
    Compute Compton-to-total ratio R(E) and equivalent atomic number Zeq(E).

    R(E)  = μ_Compton(E) / μ_total_without_coherent(E)
    Zeq   is found by log-log interpolation between reference elements
          (Phy-X / Harima 1983 method).

    xcom_compton / xcom_total_nc: optional pre-computed arrays from
    get_xcom_compound.  If None, will be fetched from NIST automatically.

    Returns (R_arr, Zeq_arr), both shape (n_energies,).
    NOTE: First call may be slow (~24 NIST element requests); all cached.
    """
    from .nist_xcom import get_xcom_element, get_xcom_compound
    energies_MeV = np.asarray(energies_MeV, float)
    n_E = len(energies_MeV)

    if xcom_compton is None or xcom_total_nc is None:
        try:
            xd = get_xcom_compound(mass_fractions, energies_MeV)
            xcom_compton  = xd.get('incoherent_cm2g',             np.zeros(n_E))
            xcom_total_nc = xd.get('total_without_coherent_cm2g', np.ones(n_E))
        except Exception:
            return np.full(n_E, float('nan')), np.full(n_E, float('nan'))

    with np.errstate(divide='ignore', invalid='ignore'):
        R_arr = np.where(xcom_total_nc > 0,
                         xcom_compton / xcom_total_nc, float('nan'))

    # Reference elements spanning Z=1–82 (standard Phy-X set)
    _REF_Z = [1, 4, 6, 7, 8, 11, 12, 13, 14, 16, 17, 19, 20, 22, 26,
              29, 40, 42, 47, 50, 56, 64, 74, 82]
    ref_r = np.zeros((len(_REF_Z), n_E))
    for j, Zref in enumerate(_REF_Z):
        try:
            xd_el = get_xcom_element(Zref, energies_MeV)
            c_el  = xd_el.get('incoherent_cm2g',             np.zeros(n_E))
            t_el  = xd_el.get('total_without_coherent_cm2g', np.ones(n_E))
            with np.errstate(divide='ignore', invalid='ignore'):
                ref_r[j] = np.where(t_el > 0, c_el / t_el, 0.0)
        except Exception:
            ref_r[j] = np.zeros(n_E)

    ref_Z_arr = np.array(_REF_Z, dtype=float)
    Zeq_arr = np.full(n_E, float('nan'))
    for i in range(n_E):
        R = float(R_arr[i])
        if not np.isfinite(R) or R <= 0:
            continue
        r_col    = ref_r[:, i]
        sort_idx = np.argsort(r_col)
        r_s = r_col[sort_idx]
        Z_s = ref_Z_arr[sort_idx]
        pos = int(np.searchsorted(r_s, R))
        if pos == 0:
            Zeq_arr[i] = float(Z_s[0])
        elif pos >= len(r_s):
            Zeq_arr[i] = float(Z_s[-1])
        else:
            r1, r2 = r_s[pos - 1], r_s[pos]
            Z1, Z2 = Z_s[pos - 1], Z_s[pos]
            if r1 <= 0 or r2 <= 0 or r1 == r2:
                Zeq_arr[i] = float(Z1)
            else:
                t = (np.log(R) - np.log(r1)) / (np.log(r2) - np.log(r1))
                Zeq_arr[i] = float(Z1 + (Z2 - Z1) * float(np.clip(t, 0.0, 1.0)))

    return R_arr, Zeq_arr


# ── Core shielding parameter calculations ────────────────────────────────────

def compute_shielding_table(
    mass_fractions: dict[str, float],
    density_g_cm3: float,
    energies_MeV: np.ndarray,
    thicknesses_cm: 'np.ndarray | None' = None,
    gp_material: str = 'Water',
) -> pd.DataFrame:
    """
    Full Phy-X shielding parameter table for a material at given energies.

    Core columns (always computed via NIST XrayMassCoef):
      Energy_keV, μ/ρ, μen/ρ, μ, μen, HVL, TVL, MFP

    Extended Phy-X columns (MAC-weighted, energy-dependent):
      Zeff(E)   — effective atomic number [MAC-weighted, Phy-X definition]
      Neff(E)   — effective electron density [el/g]
      Ceff(E)   — effective conductance [S/m]  (= Neff/Nₐ × 10⁹)
      ACS(E)    — atomic cross section [cm²/atom]
      ECS(E)    — electronic cross section [cm²/electron]
      R(E)      — Compton/total ratio [from NIST XCOM, with local cache]

    Per-thickness columns (for each x in thicknesses_cm):
      T(narrow), T(buildup), RPE%, EBF
    """
    from .nist_xcom import get_mac_compound, get_xcom_compound
    energies_MeV = np.asarray(energies_MeV, float)
    if thicknesses_cm is None:
        thicknesses_cm = np.array([])
    else:
        thicknesses_cm = np.asarray(thicknesses_cm, float)

    # ── Basic MAC / LAC
    mac, mac_en = get_mac_compound(mass_fractions, energies_MeV)
    lac    = mac * density_g_cm3
    lac_en = mac_en * density_g_cm3
    hvl  = np.log(2.0)  / np.where(lac > 1e-10, lac, 1e-10)
    tvl  = np.log(10.0) / np.where(lac > 1e-10, lac, 1e-10)
    mfp  = 1.0          / np.where(lac > 1e-10, lac, 1e-10)

    # ── Extended Phy-X parameters
    m_eff = mean_atomic_molar_mass(mass_fractions)
    try:
        zeff_E = zeff_energy_dependent(mass_fractions, energies_MeV)
    except Exception:
        zeff_E = np.full(len(energies_MeV), float('nan'))

    if np.isfinite(m_eff) and m_eff > 0:
        neff_E = zeff_E * _NA / m_eff        # electrons/g (Phy-X Neff)
        ceff_E = zeff_E / m_eff * 1e9        # S/m  (Phy-X Ceff = Neff/Nₐ × 10⁹)
        acs_E  = mac * m_eff / _NA           # cm²/atom
        with np.errstate(invalid='ignore'):
            ecs_E = np.where(zeff_E > 0, acs_E / zeff_E, float('nan'))  # cm²/electron
    else:
        neff_E = ceff_E = acs_E = ecs_E = np.full(len(energies_MeV), float('nan'))

    # ── XCOM Compton/total ratio R
    r_E = np.full(len(energies_MeV), float('nan'))
    try:
        xd = get_xcom_compound(mass_fractions, energies_MeV)
        c_arr  = xd.get('incoherent_cm2g',             None)
        tnc_arr= xd.get('total_without_coherent_cm2g', None)
        if c_arr is not None and tnc_arr is not None:
            with np.errstate(divide='ignore', invalid='ignore'):
                r_E = np.where(tnc_arr > 0, c_arr / tnc_arr, float('nan'))
    except Exception:
        _log.debug(
            "XCOM Compton/total ratio could not be computed for this material \u2014 R_E will be NaN",
            exc_info=True,
        )

    rows: list[dict] = []
    for i, E in enumerate(energies_MeV):
        row: dict = {
            'Energy_MeV':     float(E),
            'Energy_keV':     float(E * 1000),
            'μ/ρ (cm²/g)':   float(mac[i]),
            'μen/ρ (cm²/g)': float(mac_en[i]),
            'μ (cm⁻¹)':      float(lac[i]),
            'μen (cm⁻¹)':    float(lac_en[i]),
            'HVL (cm)':      float(hvl[i]),
            'TVL (cm)':      float(tvl[i]),
            'MFP (cm)':      float(mfp[i]),
            'Zeff':          float(zeff_E[i]),
            'Neff (el/g)':   float(neff_E[i]),
            'Ceff (S/m)':    float(ceff_E[i]),
            'ACS (cm²/atom)':float(acs_E[i]),
            'ECS (cm²/elec)':float(ecs_E[i]),
            'R':             float(r_E[i]),
        }
        for x in thicknesses_cm:
            mfp_depth = float(lac[i]) * float(x)
            T = float(np.exp(-lac[i] * x))
            B = gp_buildup_factor(float(E), mfp_depth, gp_material) if mfp_depth > 0 else 1.0
            row[f'T @{x:.2f}cm (narrow)']  = T
            row[f'T @{x:.2f}cm (buildup)'] = T * B
            row[f'RPE% @{x:.2f}cm']        = (1.0 - T) * 100.0
            row[f'EBF @{x:.2f}cm']         = B
        rows.append(row)

    return pd.DataFrame(rows)


def compute_transmission_vs_thickness(
    mac_cm2g: float,
    density_g_cm3: float,
    thicknesses_cm: np.ndarray,
    energy_MeV: float,
    gp_material: str = 'Water',
) -> pd.DataFrame:
    """T and RPE vs thickness at a fixed energy."""
    lac = mac_cm2g * density_g_cm3
    T = np.exp(-lac * thicknesses_cm)
    mfp_depths = lac * thicknesses_cm
    B = np.array([gp_buildup_factor(energy_MeV, float(t), gp_material) for t in mfp_depths])
    return pd.DataFrame({
        'Thickness (cm)':    thicknesses_cm,
        'μx (MFP)':          mfp_depths,
        'T (narrow beam)':   T,
        'T (with buildup)':  T * B,
        'RPE% (narrow)':     (1 - T) * 100,
        'EBF':               B,
    })


def compute_multilayer(
    layers: list[dict],
    energy_MeV: float,
) -> dict:
    """
    Compute attenuation through multiple layers at a single energy.
    Each layer: {'mass_fractions': dict, 'density_g_cm3': float, 'thickness_cm': float}
    Returns total LAC equivalent, total T, and per-layer breakdown.
    """
    from .nist_xcom import get_mac_compound
    E = np.array([energy_MeV])
    layer_results = []
    T_total = 1.0
    for lyr in layers:
        mac, _ = get_mac_compound(lyr['mass_fractions'], E)
        lac = float(mac[0]) * lyr['density_g_cm3']
        T = float(np.exp(-lac * lyr['thickness_cm']))
        T_total *= T
        layer_results.append({
            'material': lyr.get('name', '—'),
            'thickness_cm': lyr['thickness_cm'],
            'density_g_cm3': lyr['density_g_cm3'],
            'μ/ρ (cm²/g)': float(mac[0]),
            'μ (cm⁻¹)': lac,
            'HVL (cm)': float(np.log(2) / lac) if lac > 0 else 999.0,
            'T_layer': T,
        })
    T_total = max(T_total, 1e-30)
    return {
        'T_total': T_total,
        'RPE_total': (1 - T_total) * 100,
        'layers': layer_results,
    }


def compute_fnrcs(mass_fractions: dict[str, float], density_g_cm3: float) -> float:
    """
    Compute fast neutron removal cross section Σ_R (cm⁻¹).
    Σ_R = Σᵢ wᵢ × (Nₐ/Aᵢ) × σ_Rᵢ × ρ
    """
    from .nist_xcom import ATOMIC_MASS
    NA = 6.02214076e23
    sigma_R = 0.0
    for sym, wf in mass_fractions.items():
        sigma_barn = FNRCS_BARNS.get(sym, None)
        A = ATOMIC_MASS.get(sym, None)
        if sigma_barn is None or A is None:
            continue
        sigma_cm2 = sigma_barn * 1e-24
        sigma_R += wf * (NA / A) * sigma_cm2 * density_g_cm3
    return sigma_R   # cm⁻¹


def compute_fnrcs_hvl(sigma_R: float) -> tuple[float, float]:
    """Return HVL_n and TVL_n (cm) for neutrons given Σ_R in cm⁻¹."""
    if sigma_R <= 0:
        return (float('inf'), float('inf'))
    hvl_n = np.log(2) / sigma_R
    tvl_n = np.log(10) / sigma_R
    return float(hvl_n), float(tvl_n)
