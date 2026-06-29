r"""
ShieldLab G4 – Validation Report Generator
===========================================
Computes MAC, HVL, TVL for a set of NIST reference materials + energies and
compares them to published NIST values.

Run:
    cd D:\projects\ShieldLabG4
    $env:PYTHONPATH="python;ui"
    d:/uv_envs/Scripts/python.exe docs/validation/validation_report.py
"""

import sys
import pathlib
import math

# ── bootstrap ──────────────────────────────────────────────────────────────
_ROOT = pathlib.Path(__file__).resolve().parents[2]
for _p in (_ROOT / "python", _ROOT / "ui"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np
import pandas as pd

from shieldlab.physics.shielding_params import compute_shielding_table as _compute_table

# ── Reference data (NIST XCOM / XrayMassCoef, accessed 2025) ───────────────
# Format: (material_name, mass_fractions, density_g_cm3, E_MeV, nist_mac_cm2g)
_REFERENCE = [
    # --- Lead ---
    ("Lead",        {"Pb": 1.0},          11.35, 0.060,  5.021),  # XCOM 60 keV
    # K-edge at ~88 keV omitted (discontinuity; interpolation-sensitive)
    ("Lead",        {"Pb": 1.0},          11.35, 0.200,  0.999),  # XCOM 200 keV
    ("Lead",        {"Pb": 1.0},          11.35, 0.662,  0.1110),
    ("Lead",        {"Pb": 1.0},          11.35, 1.000,  0.07102),
    ("Lead",        {"Pb": 1.0},          11.35, 1.332,  0.05624),
    # --- Water ---
    ("Water",       {"H": 0.1119, "O": 0.8881}, 1.0, 0.060, 0.2058),  # XCOM
    ("Water",       {"H": 0.1119, "O": 0.8881}, 1.0, 0.100, 0.1707),
    ("Water",       {"H": 0.1119, "O": 0.8881}, 1.0, 0.662, 0.08570),
    ("Water",       {"H": 0.1119, "O": 0.8881}, 1.0, 1.000, 0.07066),
    ("Water",       {"H": 0.1119, "O": 0.8881}, 1.0, 6.000, 0.02770),
    # --- Concrete (ordinary, NIST composition) ---
    ("Concrete",    {"H":0.0221,"C":0.0020,"O":0.6574,"Na":0.0015,"Mg":0.0019,
                     "Al":0.0189,"Si":0.3040,"K":0.0100,"Ca":0.0296,"Fe":0.0041},
                    2.35, 0.060, 0.2666),  # NIST XCOM (Berger et al. 2010) mixture rule; matches Hubbell & Seltzer XrayMassCoef Tab.3
    ("Concrete",    {"H":0.0221,"C":0.0020,"O":0.6574,"Na":0.0015,"Mg":0.0019,
                     "Al":0.0189,"Si":0.3040,"K":0.0100,"Ca":0.0296,"Fe":0.0041},
                    2.35, 0.662, 0.08280),  # NIST XCOM mixture rule
    ("Concrete",    {"H":0.0221,"C":0.0020,"O":0.6574,"Na":0.0015,"Mg":0.0019,
                     "Al":0.0189,"Si":0.3040,"K":0.0100,"Ca":0.0296,"Fe":0.0041},
                    2.35, 1.332, 0.05910),  # NIST XCOM mixture rule
    # --- Aluminium ---
    ("Aluminium",   {"Al": 1.0},           2.70, 0.060,  0.2778),  # XCOM
    ("Aluminium",   {"Al": 1.0},           2.70, 0.662,  0.07551),
    ("Aluminium",   {"Al": 1.0},           2.70, 1.000,  0.06146),
    # --- Iron ---
    ("Iron",        {"Fe": 1.0},           7.87, 0.060,  1.205),   # XCOM
    ("Iron",        {"Fe": 1.0},           7.87, 0.662,  0.07357),
    ("Iron",        {"Fe": 1.0},           7.87, 1.332,  0.05180),
    # --- Copper ---
    ("Copper",      {"Cu": 1.0},           8.96, 0.060,  1.581),   # XCOM
    ("Copper",      {"Cu": 1.0},           8.96, 0.662,  0.07367),
    # --- Tungsten ---
    ("Tungsten",    {"W": 1.0},           19.30, 0.060,  3.718),   # XCOM
    ("Tungsten",    {"W": 1.0},           19.30, 0.662,  0.09827),
    ("Tungsten",    {"W": 1.0},           19.30, 1.000,  0.06514),
    # --- HDPE ---
    ("HDPE",        {"H": 0.1437, "C": 0.8563}, 0.95, 0.060, 0.1990),  # XCOM
    ("HDPE",        {"H": 0.1437, "C": 0.8563}, 0.95, 0.662, 0.08786),
    ("HDPE",        {"H": 0.1437, "C": 0.8563}, 0.95, 1.000, 0.07240),
    # --- Bismuth ---
    ("Bismuth",     {"Bi": 1.0},           9.75, 0.060,  4.540),   # XCOM
    ("Bismuth",     {"Bi": 1.0},           9.75, 0.662,  0.1133),
    ("Bismuth",     {"Bi": 1.0},           9.75, 1.332,  0.05789),

    # === Extended dataset — 26 additional points (NIST XrayMassCoef, accessed 2025) ===
    # --- Water extended ---
    ("Water",       {"H": 0.1119, "O": 0.8881}, 1.0,   5.000,  0.03031),
    ("Water",       {"H": 0.1119, "O": 0.8881}, 1.0,  10.000,  0.02219),
    # --- Aluminium extended ---
    ("Aluminium",   {"Al": 1.0},           2.70,  5.000,  0.02836),
    ("Aluminium",   {"Al": 1.0},           2.70, 10.000,  0.02318),
    # --- Concrete extended (NIST ordinary concrete composition) ---
    ("Concrete",    {"H":0.0221,"C":0.0020,"O":0.6574,"Na":0.0015,"Mg":0.0019,
                     "Al":0.0189,"Si":0.3040,"K":0.0100,"Ca":0.0296,"Fe":0.0041},
                    2.35,  5.000,  0.03045),
    ("Concrete",    {"H":0.0221,"C":0.0020,"O":0.6574,"Na":0.0015,"Mg":0.0019,
                     "Al":0.0189,"Si":0.3040,"K":0.0100,"Ca":0.0296,"Fe":0.0041},
                    2.35, 10.000,  0.02372),
    # --- Iron extended ---
    ("Iron",        {"Fe": 1.0},           7.87,  0.400,  0.09400),
    ("Iron",        {"Fe": 1.0},           7.87,  2.000,  0.04265),
    ("Iron",        {"Fe": 1.0},           7.87,  5.000,  0.03146),
    ("Iron",        {"Fe": 1.0},           7.87,  8.000,  0.02991),
    ("Iron",        {"Fe": 1.0},           7.87, 10.000,  0.02994),
    # --- Copper extended ---
    ("Copper",      {"Cu": 1.0},           8.96,  2.000,  0.04205),
    ("Copper",      {"Cu": 1.0},           8.96,  5.000,  0.03177),
    # --- HDPE extended ---
    ("HDPE",        {"H": 0.1437, "C": 0.8563}, 0.95,  5.000,  0.03044),
    ("HDPE",        {"H": 0.1437, "C": 0.8563}, 0.95, 10.000,  0.02145),
    # --- Tungsten extended ---
    ("Tungsten",    {"W": 1.0},           19.30,  0.400,  0.19250),
    ("Tungsten",    {"W": 1.0},           19.30,  2.000,  0.04433),
    ("Tungsten",    {"W": 1.0},           19.30,  5.000,  0.04103),
    ("Tungsten",    {"W": 1.0},           19.30,  8.000,  0.04472),
    ("Tungsten",    {"W": 1.0},           19.30, 10.000,  0.04747),
    # --- Lead extended ---
    ("Lead",        {"Pb": 1.0},          11.35,  0.400,  0.23230),
    ("Lead",        {"Pb": 1.0},          11.35,  2.000,  0.04606),
    ("Lead",        {"Pb": 1.0},          11.35,  5.000,  0.04272),
    ("Lead",        {"Pb": 1.0},          11.35,  8.000,  0.04675),
    ("Lead",        {"Pb": 1.0},          11.35, 10.000,  0.04972),
    # --- Bismuth non-edge control ---
    ("Bismuth",     {"Bi": 1.0},           9.75,  1.000,  0.07214),
]

_MAC_COL = "μ/ρ (cm²/g)"
_HVL_COL = "HVL (cm)"
_TVL_COL = "TVL (cm)"


def _run_one(mf: dict, rho: float, E_MeV: float) -> dict:
    E_arr = np.array([E_MeV])
    df: pd.DataFrame = _compute_table(mf, rho, E_arr)
    row = df.iloc[0]
    return {
        "mac":  float(row[_MAC_COL]),
        "hvl":  float(row[_HVL_COL]),
        "tvl":  float(row[_TVL_COL]),
    }


def build_report() -> pd.DataFrame:
    rows = []
    for mat_name, mf, rho, E_MeV, ref_mac in _REFERENCE:
        try:
            calc = _run_one(mf, rho, E_MeV)
            calc_mac = calc["mac"]
            rel_err = (calc_mac - ref_mac) / ref_mac * 100.0
            rows.append({
                "Material":       mat_name,
                "E_MeV":          E_MeV,
                "density":        rho,
                "NIST_MAC":       ref_mac,
                "Calc_MAC":       round(calc_mac, 5),
                "Rel_err_pct":    round(rel_err, 2),
                "HVL_cm":         round(calc["hvl"], 4),
                "TVL_cm":         round(calc["tvl"], 4),
                "PASS":           "PASS" if abs(rel_err) <= 16.0 else "FAIL",
            })
        except Exception as exc:
            rows.append({
                "Material":    mat_name,
                "E_MeV":       E_MeV,
                "density":     rho,
                "NIST_MAC":    ref_mac,
                "Calc_MAC":    "ERROR",
                "Rel_err_pct": None,
                "HVL_cm":      None,
                "TVL_cm":      None,
                "PASS":        f"ERROR: {exc}",
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    pd.set_option("display.max_columns", 20)
    pd.set_option("display.width",      160)
    pd.set_option("display.float_format", "{:.4f}".format)

    print("ShieldLab G4 — Validation Report")
    print("=" * 70)
    df = build_report()
    print(df.to_string(index=False))
    print()

    n_pass  = (df["PASS"] == "PASS").sum()
    n_total = len(df)
    n_fail  = n_total - n_pass
    pct     = n_pass / n_total * 100

    print(f"\nSummary: {n_pass}/{n_total} PASS ({pct:.1f}%)")
    if n_fail:
        print("\nFAILURES:")
        print(df[df["PASS"] != "PASS"][["Material", "E_MeV", "Rel_err_pct", "PASS"]].to_string(index=False))

    # CSV output
    out = _ROOT / "docs" / "validation" / "validation_report.csv"
    df.to_csv(out, index=False)
    print(f"\nCSV written to: {out}")
