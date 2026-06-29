"""NIST XrayMassCoef / XCOM data fetcher with local disk caching.

Provides photon mass attenuation coefficients μ/ρ and energy-absorption
coefficients μ_en/ρ (both in cm²/g) for elements Z=1..92.
Compounds are handled via the mixture rule:
    (μ/ρ)_mix = Σ wᵢ (μ/ρ)ᵢ

Data source: NIST Physical Reference Data
  https://physics.nist.gov/PhysRefData/XrayMassCoef/
  https://physics.nist.gov/cgi-bin/Xcom/xcom2.pl
"""
from __future__ import annotations

import re
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

import numpy as np

# ── Element lookup ────────────────────────────────────────────────────────────
_Z_TO_SYM: dict[int, str] = {
    1:'H',  2:'He', 3:'Li', 4:'Be', 5:'B',  6:'C',  7:'N',  8:'O',  9:'F',  10:'Ne',
   11:'Na',12:'Mg',13:'Al',14:'Si',15:'P', 16:'S', 17:'Cl',18:'Ar',19:'K', 20:'Ca',
   21:'Sc',22:'Ti',23:'V', 24:'Cr',25:'Mn',26:'Fe',27:'Co',28:'Ni',29:'Cu',30:'Zn',
   31:'Ga',32:'Ge',33:'As',34:'Se',35:'Br',36:'Kr',37:'Rb',38:'Sr',39:'Y', 40:'Zr',
   41:'Nb',42:'Mo',43:'Tc',44:'Ru',45:'Rh',46:'Pd',47:'Ag',48:'Cd',49:'In',50:'Sn',
   51:'Sb',52:'Te',53:'I', 54:'Xe',55:'Cs',56:'Ba',57:'La',58:'Ce',59:'Pr',60:'Nd',
   61:'Pm',62:'Sm',63:'Eu',64:'Gd',65:'Tb',66:'Dy',67:'Ho',68:'Er',69:'Tm',70:'Yb',
   71:'Lu',72:'Hf',73:'Ta',74:'W', 75:'Re',76:'Os',77:'Ir',78:'Pt',79:'Au',80:'Hg',
   81:'Tl',82:'Pb',83:'Bi',84:'Po',85:'At',86:'Rn',87:'Fr',88:'Ra',89:'Ac',90:'Th',
   91:'Pa',92:'U',
}
SYM_TO_Z: dict[str, int] = {v: k for k, v in _Z_TO_SYM.items()}

# Atomic masses (g/mol) — standard atomic weights IUPAC 2021
_ATOMIC_MASS: dict[str, float] = {
    'H':1.008,'He':4.003,'Li':6.941,'Be':9.012,'B':10.811,'C':12.011,'N':14.007,'O':15.999,
    'F':18.998,'Ne':20.180,'Na':22.990,'Mg':24.305,'Al':26.982,'Si':28.086,'P':30.974,'S':32.065,
    'Cl':35.453,'Ar':39.948,'K':39.098,'Ca':40.078,'Sc':44.956,'Ti':47.867,'V':50.942,'Cr':51.996,
    'Mn':54.938,'Fe':55.845,'Co':58.933,'Ni':58.693,'Cu':63.546,'Zn':65.38,'Ga':69.723,'Ge':72.630,
    'As':74.922,'Se':78.971,'Br':79.904,'Kr':83.798,'Rb':85.468,'Sr':87.620,'Y':88.906,'Zr':91.224,
    'Nb':92.906,'Mo':95.960,'Tc':98.000,'Ru':101.07,'Rh':102.91,'Pd':106.42,'Ag':107.87,'Cd':112.41,
    'In':114.82,'Sn':118.71,'Sb':121.76,'Te':127.60,'I':126.90,'Xe':131.29,'Cs':132.91,'Ba':137.33,
    'La':138.91,'Ce':140.12,'Pr':140.91,'Nd':144.24,'Pm':145.00,'Sm':150.36,'Eu':151.96,'Gd':157.25,
    'Tb':158.93,'Dy':162.50,'Ho':164.93,'Er':167.26,'Tm':168.93,'Yb':173.04,'Lu':174.97,'Hf':178.49,
    'Ta':180.95,'W':183.84,'Re':186.21,'Os':190.23,'Ir':192.22,'Pt':195.08,'Au':196.97,'Hg':200.59,
    'Tl':204.38,'Pb':207.20,'Bi':208.98,'Po':209.00,'At':210.00,'Rn':222.00,'Fr':223.00,'Ra':226.00,
    'Ac':227.00,'Th':232.04,'Pa':231.04,'U':238.03,
}
ATOMIC_MASS = _ATOMIC_MASS

# ── Cache directory ───────────────────────────────────────────────────────────
_CACHE_DIR = Path(__file__).parent.parent / "data" / "xcom_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Increment this string whenever the fetch/parse logic changes so that stale
# cached .npz files are automatically invalidated and re-fetched on next use.
_CACHE_VERSION = "v2"

_NIST_MAC_BASE = "https://physics.nist.gov/PhysRefData/XrayMassCoef/ElemTab"
_NIST_XCOM_CGI = "https://physics.nist.gov/cgi-bin/Xcom/xcom2.pl"

_SCI_3 = re.compile(
    r'(\d+\.\d+[Ee][+\-]?\d+)\s+(\d+\.\d+[Ee][+\-]?\d+)\s+(\d+\.\d+[Ee][+\-]?\d+)'
)


# ── Element MAC from XrayMassCoef ─────────────────────────────────────────────
def _fetch_element_mac(Z: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (energy_MeV, mu_rho_cm2g, mu_en_rho_cm2g) from NIST XrayMassCoef."""
    cache = _CACHE_DIR / f"z{Z:02d}_mac.npz"
    if cache.exists():
        d = np.load(str(cache))
        stored_version = str(d['cache_version'][0]) if 'cache_version' in d else ''
        energy_cached   = d['energy'].copy()
        mac_cached      = d['mac'].copy()
        mac_en_cached   = d['mac_en'].copy()
        d.close()
        if stored_version == _CACHE_VERSION:
            return energy_cached, mac_cached, mac_en_cached
        # Version mismatch — delete stale cache and re-fetch
        cache.unlink(missing_ok=True)

    url = f"{_NIST_MAC_BASE}/z{Z:02d}.html"
    req = urllib.request.Request(url, headers={'User-Agent': 'ShieldLabG4/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            html = r.read().decode('latin-1')
    except Exception as exc:
        raise ConnectionError(f"NIST fetch failed for Z={Z}: {exc}") from exc

    rows = [
        (float(m.group(1)), float(m.group(2)), float(m.group(3)))
        for line in html.splitlines()
        for m in [_SCI_3.search(line)] if m
    ]
    if len(rows) < 5:
        raise ValueError(f"Could not parse NIST MAC data for Z={Z}")

    arr = np.array(rows)
    energy, mac, mac_en = arr[:, 0], arr[:, 1], arr[:, 2]
    # kind='stable' preserves the HTML row order for duplicate-energy edge pairs
    # (pre-edge row comes before post-edge row in NIST tabulation).
    idx = np.argsort(energy, kind='stable')
    energy, mac, mac_en = energy[idx], mac[idx], mac_en[idx]

    np.savez(str(cache), energy=energy, mac=mac, mac_en=mac_en,
             cache_version=np.array([_CACHE_VERSION]))
    return energy, mac, mac_en


def get_mac_element(Z: int, energies_MeV: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (μ/ρ, μ_en/ρ) in cm²/g for element Z via log-log interpolation."""
    e_tab, mac_tab, mac_en_tab = _fetch_element_mac(Z)
    log_e = np.log(np.clip(np.asarray(energies_MeV, float), 1e-10, None))
    log_e_tab = np.log(np.clip(e_tab, 1e-10, None))
    log_mac = np.interp(log_e, log_e_tab,
                        np.log(np.clip(mac_tab, 1e-30, None)),
                        left=np.log(mac_tab[0]), right=np.log(mac_tab[-1]))
    log_mac_en = np.interp(log_e, log_e_tab,
                           np.log(np.clip(mac_en_tab, 1e-30, None)),
                           left=np.log(mac_en_tab[0]), right=np.log(mac_en_tab[-1]))
    return np.exp(log_mac), np.exp(log_mac_en)


# ── Full XCOM 7-component cross sections from CGI ────────────────────────────
_SCI_7 = re.compile(
    r'(\d+\.\d+[Ee][+\-]?\d+)' + (r'\s+(\d+\.\d+[Ee][+\-]?\d+)' * 6)
)

_XCOM_COLS = [
    'coherent_cm2g', 'incoherent_cm2g', 'photoelectric_cm2g',
    'pair_nuclear_cm2g', 'pair_electron_cm2g',
    'total_with_coherent_cm2g', 'total_without_coherent_cm2g',
]


def _fetch_xcom_element(Z: int) -> dict:
    """Fetch full 7-component XCOM data for element Z (with caching)."""
    import json
    cache = _CACHE_DIR / f"z{Z:02d}_xcom.json"
    if cache.exists():
        with open(cache) as f:
            return json.load(f)

    data_bytes = urllib.parse.urlencode({
        'ZNum': str(Z), 'mdi': '0', 'Output': 'on',
        'Energies': '', 'WindowXmin': '0.001', 'WindowXmax': '100000',
    }).encode()
    req = urllib.request.Request(_NIST_XCOM_CGI, data=data_bytes,
                                  headers={'User-Agent': 'ShieldLabG4/1.0',
                                           'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode('latin-1')
    except Exception as exc:
        raise ConnectionError(f"NIST XCOM CGI failed for Z={Z}: {exc}") from exc

    # Parse 7-number lines
    result: dict[str, list] = {'energy_MeV': []}
    for col in _XCOM_COLS:
        result[col] = []

    for line in html.splitlines():
        m = _SCI_7.search(line)
        if m:
            vals = [float(m.group(i + 1)) for i in range(7)]
            result['energy_MeV'].append(vals[0])
            for col, v in zip(_XCOM_COLS, vals[1:]):
                result[col].append(v)

    if len(result['energy_MeV']) < 5:
        raise ValueError(f"Could not parse XCOM data for Z={Z}")

    with open(cache, 'w') as f:
        json.dump(result, f)
    return result


def get_xcom_element(Z: int, energies_MeV: np.ndarray) -> dict[str, np.ndarray]:
    """Return all 7 XCOM cross-sections for element Z at requested energies."""
    raw = _fetch_xcom_element(Z)
    e_tab = np.array(raw['energy_MeV'])
    log_e_tab = np.log(np.clip(e_tab, 1e-10, None))
    log_e = np.log(np.clip(np.asarray(energies_MeV, float), 1e-10, None))

    out = {'energy_MeV': np.asarray(energies_MeV, float)}
    for col in _XCOM_COLS:
        tab = np.array(raw[col])
        log_tab = np.log(np.clip(tab, 1e-30, None))
        out[col] = np.exp(np.interp(log_e, log_e_tab, log_tab,
                                     left=log_tab[0], right=log_tab[-1]))
    return out


# ── Compound / mixture MAC via mixture rule ───────────────────────────────────
def get_mac_compound(
    mass_fractions: dict[str, float],
    energies_MeV: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (μ/ρ, μ_en/ρ) for a compound using the mass-fraction mixture rule."""
    energies_MeV = np.asarray(energies_MeV, float)
    mac = np.zeros_like(energies_MeV)
    mac_en = np.zeros_like(energies_MeV)
    for sym, wf in mass_fractions.items():
        Z = SYM_TO_Z.get(sym)
        if Z is None:
            continue
        m, m_en = get_mac_element(Z, energies_MeV)
        mac += wf * m
        mac_en += wf * m_en
    return mac, mac_en


def get_xcom_compound(
    mass_fractions: dict[str, float],
    energies_MeV: np.ndarray,
) -> dict[str, np.ndarray]:
    """Return all 7 XCOM cross-sections for a compound via mixture rule."""
    energies_MeV = np.asarray(energies_MeV, float)
    out: dict[str, np.ndarray] = {'energy_MeV': energies_MeV}
    for col in _XCOM_COLS:
        out[col] = np.zeros_like(energies_MeV)
    for sym, wf in mass_fractions.items():
        Z = SYM_TO_Z.get(sym)
        if Z is None:
            continue
        el_data = get_xcom_element(Z, energies_MeV)
        for col in _XCOM_COLS:
            out[col] += wf * el_data[col]
    return out


def clear_cache() -> int:
    """Delete all cached NIST files. Returns number of files removed."""
    n = 0
    for f in _CACHE_DIR.glob("*.np*"):
        f.unlink(); n += 1
    for f in _CACHE_DIR.glob("*.json"):
        f.unlink(); n += 1
    return n
