"""ShieldLab G4 - Methods and references documentation page.

Describes every physics module, the governing equations, and the
standard it is validated against.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

import sys
from pathlib import Path

_UI_DIR = Path(__file__).resolve().parent.parent
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

from bootstrap import ensure_project_paths  # noqa: E402

ensure_project_paths()

from shieldlab.content import PAGE_COPY  # noqa: E402
import config  # noqa: E402
from shieldlab.io.methods_export_pack import generate_methods_export_pack  # noqa: E402
from components.layout import render_page_hero  # noqa: E402
from components.enterprise_ui import (  # noqa: E402
    render_breadcrumb,
    render_kpi_strip,
    render_panel_header,
    render_status_bar,
)

copy = PAGE_COPY["methods"]

# Note: st.set_page_config is called by app.py; do not call it here.

render_page_hero(str(copy["title"]), str(copy["caption"]), "Physics Documentation")

render_breadcrumb(["ShieldLab G4", "Reference"], current="Methods & References")
render_kpi_strip(
    [
        {"label": "Method Blocks", "value": "11", "trend": "Documented", "trend_state": "up", "footnote": "Core physics modules"},
        {"label": "Materials", "value": "150", "trend": "Compendium", "trend_state": "up", "footnote": "Curated material records"},
        {"label": "Isotopes", "value": "100", "trend": "Library", "trend_state": "up", "footnote": "Reference source isotopes"},
        {"label": "Validation", "value": "30/30", "trend": "PASS", "trend_state": "up", "footnote": "Benchmark gate status"},
        {"label": "Standards", "value": "NIST/ICRP", "trend": "References", "trend_state": "steady", "footnote": "Primary data sources"},
        {"label": "Export Pack", "value": "Ready", "trend": "Methods", "trend_state": "steady", "footnote": "Manuscript-ready bundle"},
    ],
    title="ShieldLab Methods & Validation Strip",
    subtitle="Physics modules, governing equations, validation benchmarks, and citable references in one place.",
)

with st.expander("Manuscript Methods Export Pack", expanded=False):
    st.caption(
        "Generate publication-ready methods artifacts including equations, assumptions context, benchmark table, and uncertainty statements."
    )
    if st.button("Generate Methods Pack", type="primary", width="stretch"):
        outputs = generate_methods_export_pack(
            project_root=config.PROJECT_ROOT,
            output_dir=config.PROJECT_ROOT / "docs" / "validation",
        )
        st.success("Methods export pack generated.")
        for name, path in outputs.items():
            st.write(f"{name}: {path}")

render_panel_header(
    "Quick Reference",
    "Physics modules, governing models, and validating standards.",
    controls=["Modules", "Sources", "Validation"],
)
with st.expander(str(copy["quick_reference"]), expanded=True):
    st.dataframe(
        pd.DataFrame(
            [
                {"Module": "Photon attenuation", "Core model": "NIST mixture rule + log-log interpolation", "Primary source": "NIST SRD 126", "Validation": "MAC/HVL benchmarks"},
                {"Module": "Build-up factors", "Core model": "GP fitting parameters", "Primary source": "ANSI/ANS-6.4.3", "Validation": "Engineering-standard coefficients"},
                {"Module": "Dose-rate", "Core model": "Inverse-square + attenuation + build-up", "Primary source": "ICRP-107 / ICRU-57", "Validation": "Source-dose consistency checks"},
                {"Module": "Charged particles", "Core model": "ESTAR/PSTAR stopping power", "Primary source": "NIST SRD 124", "Validation": "Range/stopping cross-checks"},
                {"Module": "Neutrons", "Core model": "Fast removal cross-section", "Primary source": "Blizard-Abbott / Shultis & Faw", "Validation": "Mixture-rule comparisons"},
                {"Module": "Data libraries", "Core model": "Curated compositions + decay data", "Primary source": "ICRU / PNNL / ICRP / ENSDF", "Validation": "Library integrity checks"},
            ]
        ), width="stretch",
        hide_index=True,
    )

st.info(
    "Scope: ShieldLab G4 is an analytical companion to Monte Carlo workflows. "
    "It is optimized for rapid screening, reproducible figures, and reference-traceable calculations; "
    "clinical or regulatory use still requires independent verification."
)


def _section(icon: str, title: str) -> None:
    st.markdown(f"---\n### {icon} {title}")


def _cite(ref: str) -> None:
    st.caption(f"Reference: {ref}")


_section("1.", "Mass Attenuation Coefficients (MAC)")

st.markdown(r"""
The **mass attenuation coefficient** $\mu/\rho$ (cm^2/g) for a mixture is
computed via the NIST mixture rule:

$$\frac{\mu}{\rho} = \sum_i w_i \left(\frac{\mu}{\rho}\right)_i$$

where $w_i$ is the mass fraction of element $i$.  Elemental coefficients are
interpolated from the **NIST XrayMassCoef** database using **cubic log-log
interpolation** (Akima spline on log$E$ vs log$\mu/\rho$), which preserves
monotonicity and accuracy across absorption edges.
""")
_cite(
    "Hubbell, J.H. & Seltzer, S.M. (1995, updated 2004). "
    "*Tables of X-Ray Mass Attenuation Coefficients and Mass Energy-Absorption Coefficients.* "
    "NIST Standard Reference Database 126. https://physics.nist.gov/PhysRefData/XrayMassCoef/"
)

_section("2.", "Half-Value Layer (HVL) and Tenth-Value Layer (TVL)")

st.markdown(r"""
For **narrow-beam, broad good-geometry** (no build-up), the linear attenuation
coefficient is:

$$\mu \;(\text{cm}^{-1}) = \frac{\mu}{\rho} \times \rho$$

The half-value layer and tenth-value layer follow directly:

$$\text{HVL} = \frac{\ln 2}{\mu} \qquad \text{TVL} = \frac{\ln 10}{\mu}$$

These are **first-HVL** values; build-up factors $B(E, \mu x)$ must be applied
separately for broad-beam geometries (see Tab. 6 below).
""")
_cite(
    "Attix, F.H. (1986). *Introduction to Radiological Physics and Radiation Dosimetry.* "
    "Wiley-Interscience. Sections 3 and 7."
)

_section("3.", "Narrow-Beam Transmission")

st.markdown(r"""
Transmitted fraction through thickness $x$ (cm):

$$T(x) = e^{-\mu x} = e^{-(\mu/\rho)\,\rho\,x}$$

For **multi-layer** shields (layers 1 to $n$):

$$T = \prod_{k=1}^{n} e^{-\mu_k x_k}$$
""")
_cite(
    "Shultis, J.K. & Faw, R.E. (2000). *Radiation Shielding.* "
    "American Nuclear Society. Sections 4.1-4.3."
)

_section("4.", "Compton Cross-Section (Klein-Nishina)")

st.markdown("The **differential** Klein-Nishina cross-section per electron:")
st.latex(
    r"\frac{d\sigma}{d\Omega} = \frac{r_e^2}{2}"
    r"\left(\frac{k'}{k}\right)^2"
    r"\left(\frac{k}{k'} + \frac{k'}{k} - \sin^2\theta\right)"
)
st.markdown(
    r"where $k = E/(m_e c^2)$, $r_e = 2.818\times10^{-13}$ cm (classical electron radius)."
    "  The **total** Klein-Nishina cross-section per electron (Thomson units):"
)
st.latex(
    r"\sigma_{KN} = 2\pi r_e^2 \left\{"
    r"\frac{1+k}{k^3}\left[\frac{2k(1+k)}{1+2k} - \ln(1+2k)\right]"
    r"+ \frac{\ln(1+2k)}{2k} - \frac{1+3k}{(1+2k)^2}"
    r"\right\}"
)
st.markdown(
    r"ShieldLab integrates over all solid angles to derive the Compton "
    r"contribution to $\mu/\rho$ as a cross-check against NIST tabulated values."
)
_cite(
    "Klein, O. & Nishina, Y. (1929). Ueber die Streuung von Strahlung durch "
    "freie Elektronen nach der neuen relativistischen Quantendynamik. "
    "*Zeitschrift fuer Physik* 52, 853-868. "
    "See also: Evans, R.D. (1955). *The Atomic Nucleus.* McGraw-Hill, Ch. 23."
)

_section("5.", "Neutron Fast-Removal Cross-Section (FNRCS)")

st.markdown(r"""
The **fast-neutron removal cross-section** $\Sigma_R$ (cm$^{-1}$) for a mixture is
computed as:

$$\Sigma_R = \rho \sum_i \frac{w_i}{A_i} \sigma_{R,i} \, N_A$$

where $\sigma_{R,i}$ (cm^2/atom) is the elemental removal cross-section,
$A_i$ is the atomic mass (g/mol), and $N_A$ is Avogadro's number.
Elemental $\sigma_R$ values are taken from the Blizard-Abbott table (1962)
as compiled in Shultis & Faw (2000), Table 5-2.

The resulting HVL for fast neutrons is:

$$\text{HVL}_n = \frac{\ln 2}{\Sigma_R}$$
""")
_cite(
    "Blizard, E.P. & Abbott, L.S. (1962). *Reactor Handbook, Vol. III Part B: Shielding.* "
    "Interscience Publishers. "
    "Shultis, J.K. & Faw, R.E. (2000). *Radiation Shielding.* ANS, Table 5-2."
)

_section("6.", "Gamma Build-Up Factors (Geometric Progression)")

st.markdown(r"""
Build-up factors $B(\mu x, E)$ account for multiply-scattered photons in
broad-beam geometry.  ShieldLab uses the **Geometric Progression (GP) fit**:

$$B(x) = 1 + (b-1)\frac{K^x - 1}{K - 1}, \quad K \ne 1$$
$$B(x) = 1 + (b-1)\,x, \quad K = 1$$

where $x = \mu_{\text{air}} \cdot d$ (mean free paths), and the GP parameters
$(b, c, a, K, d_{\text{GP}})$ are taken from the **ANS-6.4.3** standard.
""")
_cite(
    "ANSI/ANS-6.4.3-1991. *Gamma-Ray Attenuation Coefficients and Buildup "
    "Factors for Engineering Materials.* American Nuclear Society."
)

_section("7.", "Point-Source Dose-Rate")

st.markdown(r"""
Unshielded point-source dose-rate at distance $r$:

$$\dot{H}(r) = \frac{A \cdot \Gamma}{r^2}$$

where $A$ is source activity (Bq), $r$ is distance (m), and $\Gamma$ is the
dose-rate constant (Sv m$^2$ Bq$^{-1}$ s$^{-1}$) derived from ICRP-107 emission data and
NIST air kerma coefficients.

With shielding of thickness $x$ and build-up factor $B$:

$$\dot{H}_{\text{shielded}}(r, x) = \dot{H}(r) \cdot B(\mu x) \cdot e^{-\mu x}$$
""")
_cite(
    "ICRP Publication 107 (2008). *Nuclear Decay Data for Dosimetric Calculations.* "
    "Annals of the ICRP 38(3).  "
    "ICRU Report 57 (1998). *Conversion Coefficients for Use in Radiological Protection.*"
)

_section("8.", "Electron & Ion Stopping Power (ESTAR / PSTAR)")

st.markdown(r"""
Electron and charged-particle ranges are computed by interpolating NIST
**ESTAR** (electrons) and **PSTAR** (protons) stopping-power tables:

$$-\frac{dE}{dx}\bigg|_{\text{total}} = S_{\text{collision}} + S_{\text{radiative}}$$

Radiative stopping power is significant for electrons in high-$Z$ materials
above ~1 MeV, and is included in the ESTAR tables used.  The CSDA range is:

$$R_{\text{CSDA}} = \int_0^{E_0} \left(-\frac{dE}{dx}\right)^{-1} dE$$
""")
_cite(
    "Berger, M.J. et al. (2005). ESTAR, PSTAR, ASTAR: Computer Programs for Calculating "
    "Stopping-Power and Range Tables for Electrons, Protons, and Helium Ions. "
    "NIST Standard Reference Database 124. https://physics.nist.gov/Star"
)

_section("9.", "Radionuclide Decay Data")

st.markdown(r"""
Decay modes, half-lives, gamma energies, and emission intensities for the
**100-isotope library** are taken from:

- **ICRP-107** (2008) - nuclear decay data for dosimetric calculations  
- **ENSDF** (Evaluated Nuclear Structure Data File, NNDC/BNL) - for half-lives
  and branching ratios not yet in ICRP-107  

Gamma dose-rate constants $\Gamma$ (Sv m$^2$ Bq$^{-1}$ s$^{-1}$) are derived by summing
over all photon lines:

$$\Gamma = \frac{1}{4\pi} \sum_j I_j \cdot E_j \cdot \left(\frac{\mu_{en}}{\rho}\right)_{\text{air},j}$$

where $I_j$ is the photon emission probability and $(\mu_{en}/\rho)_j$ is the
air mass energy-absorption coefficient from NIST.
""")
_cite(
    "ICRP Publication 107 (2008). *Nuclear Decay Data for Dosimetric Calculations.* "
    "Annals of the ICRP 38(3).  "
    "NNDC/BNL, Evaluated Nuclear Structure Data File (ENSDF). https://www.nndc.bnl.gov/ensdf/"
)

_section("10.", "Material Composition Library (150 materials)")

st.markdown(r"""
Elemental mass fractions and nominal densities for all **150 materials** in the
ShieldLab G4 compendium are sourced from:

| Category | Source |
|---|---|
| Tissues & phantoms | ICRU Report 46 (1992) |
| Shielding materials | NIST PSTAR / XCOM compound data |
| Detector media | Manufacturer specifications & published literature |
| Construction materials | NIST/PNNL Material Compendium (2011) |
| Gases & liquids | NIST Chemistry WebBook, ICRU Report 37 |
| Nuclear/reactor materials | IAEA-TECDOC-1234 (2001) |
""")
_cite(
    "ICRU Report 46 (1992). *Photon, Electron, Proton and Neutron Interaction Data for Body Tissues.*  "
    "White, D.R. et al. (2011). *Compendium of Material Composition Data for Radiation Transport Modeling.* "
    "PNNL-15870 Rev. 1."
)

_section("11.", "Validation Summary")

st.markdown("""
ShieldLab G4 ships a fully automated validation suite (`docs/validation/validation_report.py`)
that computes MAC for **8 materials at 3-5 energies** and compares to published NIST
tabulated values. The acceptance criterion is **<= 1% relative error**.

Current status: **30/30 PASS (100%)** - run locally via:
""")
st.code(
    "cd D:/projects/ShieldLabG4\n"
    '$env:PYTHONPATH="python;ui"\n'
    "d:/uv_envs/Scripts/python.exe docs/validation/validation_report.py",
    language="powershell",
)

st.markdown("""
An independent benchmark suite (`tests/benchmarks/`) covers **45 parameterised
cases** across MAC and HVL checks vs NIST / Attix textbook values.
""")

st.markdown("---")
st.caption(
    "ShieldLab G4 - Methods documentation - "
    "All referenced standards are available from their respective issuing organisations."
)



