"""ShieldLab G4 — Command-Line Interface.

Commands
--------
shieldlab calc        — compute shielding parameters for a material
shieldlab estar       — ESTAR electron stopping-power table
shieldlab ion         — ion stopping-power / range table
shieldlab dose-rate   — H*(10) dose-equivalent rate vs distance
shieldlab compare     — compare multiple materials
shieldlab info mat    — lookup material in NIST COMPENDIUM
shieldlab info iso    — lookup isotope in ICRP-107 library
shieldlab report      — generate a PDF report from a .shieldlab session file
shieldlab version     — print package version

Installation (in project venv):
    pip install click
    python -m cli.main --help

Or as a script:
    python D:/projects/ShieldLabG4/cli/main.py calc --help
"""
from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap PYTHONPATH
_ROOT = Path(__file__).resolve().parent.parent
for _p in [str(_ROOT / "python"), str(_ROOT / "ui")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import json
import io

import click
import numpy as np

from shieldlab import __version__

# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_material(mat_str: str) -> dict[str, float]:
    """Parse element:fraction pairs from a string like 'Pb:1.0' or 'H:0.11,O:0.89'."""
    parts = [p.strip() for p in mat_str.split(",")]
    result: dict[str, float] = {}
    for p in parts:
        if ":" not in p:
            raise click.BadParameter(
                f"Invalid material spec '{p}'. Use 'El:fraction' format, e.g. 'Pb:1.0'."
            )
        el, frac = p.split(":", 1)
        result[el.strip()] = float(frac.strip())
    return result


def _energy_array(energies_str: str | None) -> np.ndarray:
    """Parse comma-separated MeV values or 'start:stop:n' linspace spec."""
    if energies_str is None:
        from shieldlab.physics.shielding_params import XCOM_ENERGY_GRID
        return XCOM_ENERGY_GRID
    if ":" in energies_str and energies_str.count(":") == 2:
        start, stop, n = energies_str.split(":")
        return np.linspace(float(start), float(stop), int(n))
    return np.array([float(e) for e in energies_str.split(",")])


def _output(df_or_str, fmt: str, output_file: str | None) -> None:
    """Print or write DataFrame / string in the requested format."""
    import pandas as pd

    if isinstance(df_or_str, pd.DataFrame):
        if fmt == "csv":
            text = df_or_str.to_csv(index=False)
        elif fmt == "json":
            text = df_or_str.to_json(orient="records", indent=2)
        else:
            text = df_or_str.to_string(index=False)
    else:
        text = str(df_or_str)

    if output_file:
        Path(output_file).write_text(text, encoding="utf-8")
        click.echo(f"Saved to {output_file}")
    else:
        click.echo(text)


# ── CLI root ──────────────────────────────────────────────────────────────────

@click.group()
@click.version_option(__version__, prog_name="shieldlab")
def cli() -> None:
    """ShieldLab G4 — analytical radiation-shielding toolkit."""


# ── calc ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--mat",      "-m", required=True,
              help="Material as 'El:frac[,El:frac,...]', e.g. 'Pb:1.0'")
@click.option("--density",  "-d", required=True, type=float,
              help="Material density (g/cm³)")
@click.option("--energies", "-e", default=None,
              help="Energies in MeV: comma-list or 'start:stop:n'. Default: XCOM grid.")
@click.option("--gp-mat",   default="Water",
              help="G-P buildup factor material (default: Water)")
@click.option("--thickness", "-x", default=None, type=float,
              help="Optional shield thickness (cm) for T(x) output")
@click.option("--format",   "-f", "fmt", default="table",
              type=click.Choice(["table", "csv", "json"]),
              help="Output format")
@click.option("--output",   "-o", default=None,
              help="Write output to this file (default: stdout)")
def calc(mat, density, energies, gp_mat, thickness, fmt, output) -> None:
    """Compute MAC, LAC, HVL, TVL, MFP, EBF for a material."""
    try:
        mf = _parse_material(mat)
        E  = _energy_array(energies)
        from shieldlab.physics.shielding_params import compute_shielding_table
        df = compute_shielding_table(mf, density, E, gp_mat=gp_mat, thickness_cm=thickness)
        _output(df, fmt, output)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


# ── estar ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--mat",      "-m", required=True, help="Material spec")
@click.option("--density",  "-d", required=True, type=float)
@click.option("--energies", "-e", default=None, help="Electron energies (MeV)")
@click.option("--format",   "-f", "fmt", default="table",
              type=click.Choice(["table", "csv", "json"]))
@click.option("--output",   "-o", default=None)
def estar(mat, density, energies, fmt, output) -> None:
    """Compute ESTAR electron stopping-power table."""
    try:
        mf = _parse_material(mat)
        E  = _energy_array(energies)
        from shieldlab.physics.nist_estar import compute_estar_table
        df = compute_estar_table(mf, density, E)
        _output(df, fmt, output)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


# ── ion ───────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--mat",      "-m", required=True, help="Material spec")
@click.option("--density",  "-d", required=True, type=float)
@click.option("--particle", "-p", default="proton",
              help="'proton', 'alpha', or 'Z:A' for heavy ion")
@click.option("--energies", "-e", default=None,
              help="Energies in MeV/u (comma-list or start:stop:n)")
@click.option("--format",   "-f", "fmt", default="table",
              type=click.Choice(["table", "csv", "json"]))
@click.option("--output",   "-o", default=None)
def ion(mat, density, particle, energies, fmt, output) -> None:
    """Compute ion stopping power and range (Bethe-Bloch / PSTAR / ASTAR)."""
    try:
        mf = _parse_material(mat)
        E  = _energy_array(energies)
        from shieldlab.physics.ion_range import compute_ion_table
        df = compute_ion_table(mf, density, particle, E)
        _output(df, fmt, output)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


# ── dose-rate ─────────────────────────────────────────────────────────────────

@cli.command("dose-rate")
@click.option("--activity", "-a", required=True, type=float,
              help="Activity in Bq")
@click.option("--energy",   "-e", required=True, type=float,
              help="Photon energy (MeV)")
@click.option("--intensity", "-i", default=1.0, type=float,
              help="Photon yield per disintegration (default 1.0)")
@click.option("--distances", default="0.1,0.5,1.0,2.0,5.0,10.0",
              help="Comma-separated distances in metres")
@click.option("--format",   "-f", "fmt", default="table",
              type=click.Choice(["table", "csv", "json"]))
@click.option("--output",   "-o", default=None)
def dose_rate_cmd(activity, energy, intensity, distances, fmt, output) -> None:
    """Compute H*(10) dose-equivalent rate vs distance for a point source."""
    try:
        ds = np.array([float(x) for x in distances.split(",")])
        from shieldlab.physics.dose_rate import dose_rate_point
        import pandas as pd
        rows = []
        for d_m in ds:
            H = dose_rate_point(activity, np.array([energy]), np.array([intensity]),
                                d_m * 100.0)
            rows.append({"Distance_m": d_m, "H_star10_uSv_h": round(H, 8)})
        _output(pd.DataFrame(rows), fmt, output)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


# ── compare ───────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--mats", "-m", required=True,
              help="Semicolon-separated list of 'name=El:frac[,El:frac];density' entries, e.g. "
                   "'Lead=Pb:1.0;11.35|Water=H:0.111,O:0.889;1.0'")
@click.option("--energies", "-e", default=None)
@click.option("--format",   "-f", "fmt", default="table",
              type=click.Choice(["table", "csv", "json"]))
@click.option("--output",   "-o", default=None)
def compare(mats, energies, fmt, output) -> None:
    """Compare MAC, HVL, TVL for multiple materials."""
    try:
        import pandas as pd
        from shieldlab.physics.shielding_params import compute_shielding_table
        E = _energy_array(energies)
        entries = mats.split("|")
        frames = []
        for entry in entries:
            # Format: "name=El:frac[,El:frac];density"
            name_spec, density_str = entry.rsplit(";", 1)
            name, mat_spec = name_spec.split("=", 1)
            mf  = _parse_material(mat_spec)
            rho = float(density_str)
            df  = compute_shielding_table(mf, rho, E)
            df.insert(0, "Material", name)
            df.insert(1, "Density_g_cm3", rho)
            frames.append(df)
        combined = pd.concat(frames, ignore_index=True)
        _output(combined, fmt, output)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


# ── info ──────────────────────────────────────────────────────────────────────

@cli.group()
def info() -> None:
    """Look up materials and isotopes in built-in databases."""


@info.command("mat")
@click.argument("query")
@click.option("--category", "-c", default=None,
              help="Filter by category: tissue/construction/shielding/detector/gas/polymer/other")
def info_mat(query, category) -> None:
    """Look up a material in the NIST COMPENDIUM."""
    from shieldlab.data.compendium import search
    results = search(query, category=category)
    if not results:
        click.echo(f"No match for '{query}'.")
        return
    for m in results:
        click.echo(f"\n{m['name']}  ({m['category']})")
        click.echo(f"  Formula : {m['formula'] or 'mixture'}")
        click.echo(f"  Density : {m['density']} g/cm³")
        click.echo(f"  Ref     : {m['reference']}")
        fracs = ", ".join(f"{el}:{wf:.4f}" for el, wf in m["mass_fracs"].items())
        click.echo(f"  Fracs   : {fracs}")


@info.command("iso")
@click.argument("symbol")
def info_iso(symbol) -> None:
    """Look up an isotope in the ICRP-107 library."""
    from shieldlab.data.isotopes import get_by_symbol, half_life_str
    iso = get_by_symbol(symbol)
    if iso is None:
        click.echo(f"Isotope '{symbol}' not found in library.")
        return
    click.echo(f"\n{iso['symbol']}  (Z={iso['Z']}, A={iso['A']})")
    click.echo(f"  Half-life  : {half_life_str(iso['half_life_s'])}")
    click.echo(f"  Decay mode : {', '.join(iso['decay_mode'])}")
    click.echo(f"  Category   : {iso['category']}")
    click.echo(f"  Notes      : {iso['notes']}")
    if iso["gammas"]:
        click.echo("  Gammas:")
        for e, i in iso["gammas"]:
            click.echo(f"    {e*1000:.1f} keV  I={i:.4f}")
    if iso["betas"]:
        click.echo("  Betas (endpoint):")
        for e, i in iso["betas"]:
            click.echo(f"    {e*1000:.1f} keV  I={i:.4f}")


# ── report ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("session_file", type=click.Path(exists=True))
@click.option("--output", "-o", default=None,
              help="Output PDF path (default: same name as session file with .pdf extension)")
def report(session_file, output) -> None:
    """Generate a PDF report from a saved .shieldlab session file."""
    try:
        from shieldlab.io.session import load_session
        from shieldlab.report.pdf_report import pdf_bytes

        cs = load_session(session_file)
        data = pdf_bytes(cs, {}, version=__version__)
        out_path = output or str(Path(session_file).with_suffix(".pdf"))
        Path(out_path).write_bytes(data)
        click.echo(f"PDF report saved: {out_path}  ({len(data):,} bytes)")
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
