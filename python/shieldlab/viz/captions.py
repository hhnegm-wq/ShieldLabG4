"""Auto-generate figure captions for ShieldLab G4 outputs.

Each helper function returns a plain-text string suitable for use as a
``st.caption(...)`` call or embedded in a PDF report.

All captions follow the style recommended for Q1 radiation-physics journals:
  "Fig. N. <What is plotted> of <material> (<key parameters>) vs <x-axis>.
   Computed with ShieldLab G4 vX.Y.Z using <data source>."
"""

from __future__ import annotations

from shieldlab import __version__
from shieldlab.metadata import PRODUCT_NAME

_VER = __version__
_TOOL = f"{PRODUCT_NAME} v{_VER}"
_XCOM_SRC = "NIST XCOM / XrayMassCoef databases"
_ESTAR_SRC = "NIST ESTAR database (Bethe-Bloch, ICRU 37)"
_ION_SRC   = "NIST PSTAR/ASTAR (Bethe-Bloch + ZBL nuclear, ICRU 49)"
_FNRCS_SRC = "Shultis & Faw (2000) removal cross-section data"


def caption_mac(
    material: str,
    density: float,
    energy_range: str = "",
    fig_num: int | str = "",
) -> str:
    """Caption for a mass attenuation coefficient (MAC) vs energy plot."""
    prefix = f"Fig. {fig_num}. " if fig_num else ""
    e_str  = f" over {energy_range}" if energy_range else ""
    return (
        f"{prefix}Mass attenuation coefficient (MAC, μ/ρ) of {material} "
        f"(ρ = {density:.3f} g cm⁻³) as a function of photon energy{e_str}. "
        f"Data retrieved from {_XCOM_SRC}. Computed with {_TOOL}."
    )


def caption_hvl_tvl(
    material: str,
    density: float,
    fig_num: int | str = "",
) -> str:
    """Caption for HVL / TVL vs energy plot."""
    prefix = f"Fig. {fig_num}. " if fig_num else ""
    return (
        f"{prefix}Half-value layer (HVL) and tenth-value layer (TVL) of "
        f"{material} (ρ = {density:.3f} g cm⁻³) as a function of photon energy. "
        f"Calculated via the narrow-beam attenuation law using MAC data from "
        f"{_XCOM_SRC}. Computed with {_TOOL}."
    )


def caption_transmission(
    material: str,
    density: float,
    energy_keV: float,
    fig_num: int | str = "",
) -> str:
    """Caption for transmission vs thickness at a single energy."""
    prefix = f"Fig. {fig_num}. " if fig_num else ""
    return (
        f"{prefix}Photon transmission through {material} "
        f"(ρ = {density:.3f} g cm⁻³) as a function of shield thickness at "
        f"{energy_keV:.1f} keV. Buildup factors computed by the G-P method "
        f"(ANSI/ANS-6.4.3). Data from {_XCOM_SRC}. Computed with {_TOOL}."
    )


def caption_xcom(
    material: str,
    density: float,
    fig_num: int | str = "",
) -> str:
    """Caption for XCOM cross-section component plot."""
    prefix = f"Fig. {fig_num}. " if fig_num else ""
    return (
        f"{prefix}Photon interaction cross-section components for {material} "
        f"(ρ = {density:.3f} g cm⁻³): coherent scattering, Compton "
        f"(incoherent) scattering, photoelectric absorption, and pair "
        f"production (nuclear + electron field). Data from {_XCOM_SRC}. "
        f"Computed with {_TOOL}."
    )


def caption_estar(
    material: str,
    density: float,
    fig_num: int | str = "",
) -> str:
    """Caption for electron stopping power / CSDA range plot."""
    prefix = f"Fig. {fig_num}. " if fig_num else ""
    return (
        f"{prefix}Collision and radiative stopping powers and CSDA range for "
        f"electrons in {material} (ρ = {density:.3f} g cm⁻³) as a function "
        f"of electron kinetic energy. Computed using the Bethe-Bloch formula "
        f"with Sternheimer density-effect correction (ICRU 37). Reference: "
        f"{_ESTAR_SRC}. Computed with {_TOOL}."
    )


def caption_ion_range(
    material: str,
    density: float,
    ion: str = "proton",
    fig_num: int | str = "",
) -> str:
    """Caption for ion stopping power / CSDA range plot."""
    prefix = f"Fig. {fig_num}. " if fig_num else ""
    ion_cap = ion.capitalize()
    return (
        f"{prefix}Total stopping power and CSDA range for {ion_cap}s in "
        f"{material} (ρ = {density:.3f} g cm⁻³) as a function of kinetic "
        f"energy. Electronic stopping: Bethe-Bloch + Bragg-Kleeman compound "
        f"mean excitation energy (ICRU 49). Nuclear stopping: ZBL universal "
        f"potential. Reference: {_ION_SRC}. Computed with {_TOOL}."
    )


def caption_fnrcs(
    material: str,
    density: float,
    fig_num: int | str = "",
) -> str:
    """Caption for fast neutron removal cross section result."""
    prefix = f"Fig. {fig_num}. " if fig_num else ""
    return (
        f"{prefix}Fast neutron transmission through {material} "
        f"(ρ = {density:.3f} g cm⁻³) as a function of shield thickness, "
        f"computed from the fast neutron removal cross section (FNRCS / NGCal). "
        f"Elemental removal cross sections from {_FNRCS_SRC}. "
        f"Computed with {_TOOL}."
    )


def caption_multilayer(
    layer_names: list[str],
    fig_num: int | str = "",
) -> str:
    """Caption for a multi-layer composite shielding geometry."""
    prefix = f"Fig. {fig_num}. " if fig_num else ""
    layers_str = " / ".join(layer_names)
    return (
        f"{prefix}Two-dimensional cross-section schematic of the composite "
        f"shielding stack ({layers_str}). Layer thicknesses and densities as "
        f"specified. Computed with {_TOOL}."
    )


def caption_geometry(
    layer_names: list[str],
    particle: str,
    energy_label: str,
    fig_num: int | str = "",
) -> str:
    """Caption for a shielding geometry schematic."""
    prefix = f"Fig. {fig_num}. " if fig_num else ""
    layers_str = " / ".join(layer_names)
    return (
        f"{prefix}Schematic cross-section of the {particle} shielding "
        f"geometry: {layers_str}. Source energy: {energy_label}. "
        f"Computed with {_TOOL}."
    )


def auto_caption(
    plot_type: str,
    material: str = "",
    density: float = 0.0,
    energy_keV: float = 0.0,
    energy_range: str = "",
    ion: str = "proton",
    layer_names: list[str] | None = None,
    particle: str = "gamma",
    energy_label: str = "",
    fig_num: int | str = "",
) -> str:
    """Dispatch to the correct caption generator based on *plot_type*.

    Parameters
    ----------
    plot_type : one of "mac", "hvl_tvl", "transmission", "xcom", "estar",
                "ion_range", "fnrcs", "multilayer", "geometry"
    """
    dispatch = {
        "mac":          lambda: caption_mac(material, density, energy_range, fig_num),
        "hvl_tvl":      lambda: caption_hvl_tvl(material, density, fig_num),
        "transmission": lambda: caption_transmission(material, density, energy_keV, fig_num),
        "xcom":         lambda: caption_xcom(material, density, fig_num),
        "estar":        lambda: caption_estar(material, density, fig_num),
        "ion_range":    lambda: caption_ion_range(material, density, ion, fig_num),
        "fnrcs":        lambda: caption_fnrcs(material, density, fig_num),
        "multilayer":   lambda: caption_multilayer(layer_names or [], fig_num),
        "geometry":     lambda: caption_geometry(layer_names or [], particle, energy_label, fig_num),
    }
    fn = dispatch.get(plot_type.lower())
    if fn is None:
        return f"Figure generated with {_TOOL}."
    return fn()
