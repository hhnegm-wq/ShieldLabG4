"""2D geometry cross-section visualizer for shielding setups.

Produces matplotlib figures showing: source, beam, shield layers, detector.
Inspired by MCNP/GEANT4 geometry schematics and Phy-X layout visualizations.
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

# ── Layer colour palette ───────────────────────────────────────────────────────
_LAYER_COLORS = [
    '#2f80c9', '#8fb8de', '#5aa469', '#d8963f',
    '#7a6bc4', '#2aa7a0', '#c75d5d', '#6b7a90',
]

# ── Source symbols ─────────────────────────────────────────────────────────────
_SOURCE_COLORS = {
    'gamma':   ('#f6c915', 'γ'),
    'e-':      ('#2f80c9', 'e⁻'),
    'e+':      ('#d65252', 'e⁺'),
    'proton':  ('#d8963f', 'p'),
    'alpha':   ('#5aa469', 'α'),
    'neutron': ('#7b8794', 'n'),
    'mu-':     ('#7a6bc4', 'μ⁻'),
    'ion':     ('#2aa7a0', 'ion'),
}


def plot_shielding_geometry(
    layers: list[dict],
    particle: str = 'gamma',
    energy_label: str = '',
    show_dimensions: bool = True,
    figsize: tuple = (12.5, 4.8),
) -> plt.Figure:
    """
    Draw a 2D cross-section schematic of the shielding setup.

    Parameters
    ----------
    layers : list of dicts, each with keys:
        name (str), thickness_cm (float), density_g_cm3 (float, optional),
        color (str, optional)
    particle : Geant4 particle name (gamma, e-, proton, neutron, alpha, ...)
    energy_label : e.g. "662 keV" to label the beam
    show_dimensions : add thickness dimension lines below each layer
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=150)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#f7fafc')

    clean_layers = [lyr for lyr in layers if float(lyr.get('thickness_cm', 0.0)) > 0]
    if not clean_layers:
        clean_layers = [{'name': 'Shield', 'thickness_cm': 1.0, 'density_g_cm3': None}]
    total_thick = max(sum(float(lyr.get('thickness_cm', 1.0)) for lyr in clean_layers), 1e-6)

    from matplotlib.patches import Rectangle

    # Coordinate system is schematic, with layer widths proportional to thickness.
    source_x = 0.75
    collimator_x = 1.80
    shield_x = 2.65
    shield_w = 7.20
    detector_x = shield_x + shield_w + 0.95
    detector_w = 0.52
    y_mid = 0.52
    shield_h = 0.50
    beam_h = 0.055
    world_x0 = 0.25
    world_w = detector_x + detector_w + 0.55 - world_x0

    # World / air envelope, matching the way Geant4 users think about the setup.
    world = mpatches.FancyBboxPatch(
        (world_x0, 0.12), world_w, 0.76,
        boxstyle='round,pad=0.02,rounding_size=0.035',
        facecolor='#ffffff', edgecolor='#d7e1ec', lw=1.0, zorder=0,
    )
    ax.add_patch(world)
    ax.text(world_x0 + 0.12, 0.84, 'Air / world volume', ha='left', va='center',
            color='#6b7a90', fontsize=7.8, fontweight='semibold')

    # Source plane and collimator aperture.
    src_col, src_label = _SOURCE_COLORS.get(particle, ('#f6c915', particle))
    src_border = {'gamma': '#c6a500', 'alpha': '#a04000', 'e-': '#0055bb',
                  'e+': '#bb0000', 'neutron': '#2a7020', 'proton': '#800080'}.get(particle, '#c6a500')
    source = mpatches.FancyBboxPatch(
        (source_x, y_mid - 0.22), 0.58, 0.44,
        boxstyle='round,pad=0.025,rounding_size=0.025',
        facecolor=src_col, edgecolor=src_border, lw=1.5, zorder=4,
    )
    ax.add_patch(source)
    ax.text(source_x + 0.29, y_mid + 0.22 + 0.045, 'Source', ha='center', va='center',
            color='#46566b', fontsize=7.2, fontweight='semibold', zorder=5)
    ax.text(source_x + 0.29, y_mid + 0.07, '☢', ha='center', va='center',
            color='#17263a', fontsize=12.0, zorder=5)
    ax.text(source_x + 0.29, y_mid - 0.09, src_label, ha='center', va='center',
            color='#17263a', fontsize=8.5, fontweight='bold', zorder=5)
    if energy_label:
        ax.text(source_x + 0.29, y_mid - 0.30, energy_label, ha='center', va='center',
                color='#46566b', fontsize=7.3, zorder=5)

    # Collimator: two solid blocks with beam aperture gap between them.
    aperture_half = 0.055
    coll_top_h = 0.22 - aperture_half
    coll_bot_h = 0.22 - aperture_half
    coll_top = Rectangle((collimator_x, y_mid + aperture_half), 0.30, coll_top_h,
                          facecolor='#26384d', edgecolor='#17263a', lw=1.0, zorder=4)
    coll_bot = Rectangle((collimator_x, y_mid - aperture_half - coll_bot_h), 0.30, coll_bot_h,
                          facecolor='#26384d', edgecolor='#17263a', lw=1.0, zorder=4)
    ax.add_patch(coll_top)
    ax.add_patch(coll_bot)
    ax.text(collimator_x + 0.15, y_mid + aperture_half + coll_top_h + 0.045, 'Collimator',
            ha='center', va='center', color='#46566b', fontsize=7.2, fontweight='semibold')

    # Radiation emission fan from source (standard physics diagram convention).
    fan_angles = np.radians(np.linspace(-35, 35, 6))
    src_right_edge = source_x + 0.58
    coll_left = collimator_x - 0.05
    for angle in fan_angles:
        # Fan line from source right edge to just before collimator.
        end_y = y_mid + (coll_left - src_right_edge) * np.tan(angle)
        ax.plot([src_right_edge, coll_left], [y_mid, end_y],
                color=src_col, lw=0.7, alpha=0.45, linestyle='--', zorder=2)

    # Incident and transmitted narrow beam.
    beam_start = source_x + 0.58
    beam_end = detector_x + detector_w * 0.5
    # Pre-shield beam (full intensity)
    beam_pre = Rectangle((beam_start, y_mid - beam_h), shield_x - beam_start, 2 * beam_h,
                         facecolor='#f6c915', edgecolor='none', alpha=0.22, zorder=1)
    # Post-shield beam (attenuated — narrower/fainter)
    beam_post = Rectangle((shield_x + shield_w, y_mid - beam_h * 0.55),
                          beam_end - (shield_x + shield_w), 2 * beam_h * 0.55,
                          facecolor='#f6c915', edgecolor='none', alpha=0.12, zorder=1)
    ax.add_patch(beam_pre)
    ax.add_patch(beam_post)
    for offset, alpha in [(-0.035, 0.62), (0.0, 0.90), (0.035, 0.62)]:
        ax.add_patch(FancyArrowPatch(
            (beam_start + 0.06, y_mid + offset), (beam_end - 0.08, y_mid + offset),
            arrowstyle='->', mutation_scale=8, linewidth=1.0,
            color='#c8a00f', alpha=alpha, zorder=3,
        ))
    ax.text((source_x + collimator_x) / 2 + 0.25, y_mid + 0.115, r'$I_0$', ha='center',
            color='#4d5d72', fontsize=8.5, fontweight='bold')
    ax.text(detector_x + detector_w / 2, y_mid + 0.19, r'$I$', ha='center',
            color='#4d5d72', fontsize=8.5, fontweight='bold')

    # Shield stack with proportional layer widths and visible material boundaries.
    x = shield_x
    boundary_positions = [shield_x]
    for index, lyr in enumerate(clean_layers):
        thickness = float(lyr.get('thickness_cm', 1.0))
        width = max((thickness / total_thick) * shield_w, 0.10)
        if index == len(clean_layers) - 1:
            width = shield_x + shield_w - x
        color = lyr.get('color', _LAYER_COLORS[index % len(_LAYER_COLORS)])
        rho = lyr.get('density_g_cm3', None)
        mat_name = str(lyr.get('name', lyr.get('material', f'Layer {index + 1}')))

        layer_rect = Rectangle((x, y_mid - shield_h / 2), width, shield_h,
                               facecolor=color, edgecolor='#ffffff', lw=1.15, alpha=0.96, zorder=2)
        # IAEA-style diagonal hatching over the layer (light overlay).
        hatch_rect = Rectangle((x, y_mid - shield_h / 2), width, shield_h,
                               facecolor='none', edgecolor='#3a3a3a',
                               hatch='///', lw=0.0, alpha=0.28, zorder=3)
        ax.add_patch(layer_rect)
        ax.add_patch(hatch_rect)
        ax.plot([x, x], [y_mid - shield_h / 2, y_mid + shield_h / 2], color='#dce7f1', lw=0.8, zorder=3)

        label = f'{mat_name}\n{thickness:.2f} cm'
        if rho:
            label += f'\nρ = {float(rho):.2f} g/cm³'
        text_color = '#ffffff' if index % 2 == 0 else '#14283d'
        font_size = 7.2 if len(clean_layers) > 3 else 8.6
        label_y = y_mid + 0.12 if len(clean_layers) == 1 else y_mid
        ax.text(x + width / 2, label_y, label, ha='center', va='center', color=text_color,
            fontsize=font_size, fontweight='bold', zorder=5, linespacing=1.2,
            bbox=dict(boxstyle='round,pad=0.14', facecolor=color,
                  edgecolor='none', alpha=0.78))

        if show_dimensions:
            dim_y = y_mid - shield_h / 2 - 0.085
            ax.annotate('', xy=(x + width, dim_y), xytext=(x, dim_y),
                        arrowprops=dict(arrowstyle='<->', color='#7a8797', lw=0.8))
            ax.text(x + width / 2, dim_y - 0.035, f'{thickness:.2f} cm', ha='center', va='top',
                    color='#5d6c7d', fontsize=6.7)
        x += width
        boundary_positions.append(x)

    ax.plot([shield_x + shield_w, shield_x + shield_w],
            [y_mid - shield_h / 2, y_mid + shield_h / 2], color='#dce7f1', lw=0.8, zorder=3)
    ax.text(shield_x + shield_w / 2, y_mid + shield_h / 2 + 0.065,
            'Shield slab / layer stack', ha='center', va='center',
            color='#22384d', fontsize=8.2, fontweight='bold')

    # Detector plane / sensitive detector.
    detector = mpatches.FancyBboxPatch(
        (detector_x, y_mid - 0.20), detector_w, 0.40,
        boxstyle='round,pad=0.025,rounding_size=0.025',
        facecolor='#2aa889', edgecolor='#16826a', lw=1.0, zorder=4,
    )
    ax.add_patch(detector)
    ax.text(detector_x + detector_w / 2, y_mid, 'Detector\nplane', ha='center', va='center',
            color='#ffffff', fontsize=7.5, fontweight='bold', zorder=5)
    ax.text(detector_x + detector_w / 2, y_mid - 0.285, 'scoring volume', ha='center', va='center',
            color='#5d6c7d', fontsize=6.8)

    # Standard attenuation statement, separated from the dimension annotation.
    ax.text(detector_x - 0.25, 0.82,
        r'Narrow beam: $I = I_0\,\exp\left(-\sum_i \mu_i x_i\right)$',
        ha='right', va='center', color='#46566b', fontsize=7.9,
        bbox=dict(boxstyle='round,pad=0.28', facecolor='#f3f7fb', edgecolor='#d8e3ee'))

    ax.set_xlim(0, detector_x + detector_w + 0.75)
    ax.set_ylim(0.05, 0.95)
    ax.axis('off')

    layer_summary = ' + '.join(
        f"{lyr.get('name', lyr.get('material', '?'))} {float(lyr.get('thickness_cm', 1.0)):.2f} cm"
        for lyr in clean_layers
    )
    title = f'Shielding geometry (source - collimator - shield - detector): {layer_summary}'
    ax.set_title(title, color='#22384d', fontsize=11.4, fontweight='semibold', pad=8)

    fig.tight_layout(pad=0.9)
    return fig


def plot_mac_vs_energy(
    energies_MeV: np.ndarray,
    mac_total: np.ndarray,
    mac_en: np.ndarray | None = None,
    material_name: str = '',
    xcom_components: dict | None = None,
) -> plt.Figure:
    """
    Plot MAC (and optionally all XCOM components) vs photon energy.
    Similar to XCOM web output.
    """
    fig, ax = plt.subplots(figsize=(9, 5))
    E_keV = energies_MeV * 1000

    ax.loglog(E_keV, mac_total, 'k-', lw=2, label='Total μ/ρ (with coherent)')
    if mac_en is not None:
        ax.loglog(E_keV, mac_en, 'k--', lw=1.5, label='μ_en/ρ (energy absorption)')

    if xcom_components:
        comp_styles = {
            'coherent_cm2g':           ('C0', '--', 'Coherent scattering'),
            'incoherent_cm2g':         ('C1', '--', 'Incoherent scattering'),
            'photoelectric_cm2g':      ('C2', '--', 'Photoelectric absorption'),
            'pair_nuclear_cm2g':       ('C3', '--', 'Pair production (nuclear)'),
            'pair_electron_cm2g':      ('C4', '--', 'Pair production (electron)'),
        }
        for key, (color, ls, label) in comp_styles.items():
            if key in xcom_components:
                vals = np.array(xcom_components[key])
                mask = vals > 1e-12
                if mask.sum() > 1:
                    ax.loglog(E_keV[mask], vals[mask], color=color, ls=ls, lw=1.2, label=label)

    ax.set_xlabel('Photon Energy (keV)', fontsize=11)
    ax.set_ylabel('μ/ρ  (cm²/g)', fontsize=11)
    title = f'Mass Attenuation Coefficients'
    if material_name:
        title += f' — {material_name}'
    ax.set_title(title, fontsize=12)
    ax.legend(fontsize=8, loc='best')
    ax.grid(True, which='both', alpha=0.3)
    ax.set_xlim(E_keV.min() * 0.8, E_keV.max() * 1.2)
    fig.tight_layout()
    return fig


def plot_hvl_tvl_vs_energy(
    energies_MeV: np.ndarray,
    hvl_cm: np.ndarray,
    tvl_cm: np.ndarray,
    material_name: str = '',
) -> plt.Figure:
    """Plot HVL and TVL vs photon energy (keV)."""
    fig, ax = plt.subplots(figsize=(9, 5))
    E_keV = energies_MeV * 1000
    ax.loglog(E_keV, hvl_cm, 'b-', lw=2, label='HVL (Half Value Layer)')
    ax.loglog(E_keV, tvl_cm, 'r-', lw=2, label='TVL (Tenth Value Layer)')
    ax.set_xlabel('Photon Energy (keV)', fontsize=11)
    ax.set_ylabel('Thickness  (cm)', fontsize=11)
    title = 'HVL and TVL vs Energy'
    if material_name:
        title += f' — {material_name}'
    ax.set_title(title, fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, which='both', alpha=0.3)
    fig.tight_layout()
    return fig


def plot_transmission_vs_thickness(
    thicknesses_cm: np.ndarray,
    T_narrow: np.ndarray,
    T_buildup: np.ndarray | None = None,
    material_name: str = '',
    energy_label: str = '',
) -> plt.Figure:
    """Plot transmission T vs shield thickness (narrow beam & with buildup)."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    label_extra = f' — {material_name}' if material_name else ''
    if energy_label:
        label_extra += f' @ {energy_label}'

    # Linear scale
    axes[0].plot(thicknesses_cm, T_narrow * 100, 'b-', lw=2, label='Narrow beam')
    if T_buildup is not None:
        axes[0].plot(thicknesses_cm, T_buildup * 100, 'r--', lw=2, label='With buildup (G-P)')
    axes[0].set_xlabel('Thickness (cm)', fontsize=11)
    axes[0].set_ylabel('Transmission (%)', fontsize=11)
    axes[0].set_title(f'Transmission vs Thickness{label_extra}', fontsize=11)
    axes[0].set_ylim(-2, 102)
    axes[0].legend(fontsize=9)
    axes[0].grid(alpha=0.3)

    # Log scale
    mask = T_narrow > 1e-8
    axes[1].semilogy(thicknesses_cm[mask], T_narrow[mask], 'b-', lw=2, label='Narrow beam')
    if T_buildup is not None:
        mask2 = T_buildup > 1e-8
        axes[1].semilogy(thicknesses_cm[mask2], T_buildup[mask2], 'r--', lw=2,
                         label='With buildup (G-P)')
    axes[1].set_xlabel('Thickness (cm)', fontsize=11)
    axes[1].set_ylabel('Transmission (log scale)', fontsize=11)
    axes[1].set_title(f'Transmission (log) vs Thickness{label_extra}', fontsize=11)
    axes[1].legend(fontsize=9)
    axes[1].grid(True, which='both', alpha=0.3)

    fig.tight_layout()
    return fig
