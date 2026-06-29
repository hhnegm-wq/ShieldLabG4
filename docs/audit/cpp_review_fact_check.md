# ShieldLab G4 C++ Review Fact Check

This table corrects and updates the previously supplied C++ review against the current repository state.

| # | Review Item | Verdict | Current Status | Action |
|---|-------------|---------|----------------|--------|
| 1 | `G4RunManagerType::Serial` hardcoded | Confirmed | The original concern was valid. Serial was hardcoded in `app/ShieldLabG4.cc`. | Fixed. The run-manager mode is now configurable via `SHIELDLAB_RUN_MANAGER` with `serial`, `default`/`auto`, and `mt` when the linked Geant4 build supports multithreading. |
| 2 | Primary particle type silently stays gamma because there is no `/gun/particle` command | Incorrect | `G4ParticleGun` already exposes `/gun/particle`, and the example macro uses it explicitly. The constructor defaults to gamma at 662 keV until the macro overrides it. | No code change required. The accurate statement is that gamma and 662 keV are defaults, not hard constraints. |
| 3 | `fTransmitted` and `fReflected` only count `trackID == 1` | Confirmed | The code counts only the primary track at the world boundary. This is a semantic limitation, not a parser or crash bug. | Partially addressed. `run_summary.csv` now states that the transport count basis is `primary_track_world_boundary`, making the limitation explicit in exported results. |
| 4 | Attenuation estimate is simple Beer-Lambert with no buildup correction | Confirmed | The Monte Carlo summary still derives `mu` from primary transmission without a buildup correction model. This is a design limitation rather than an implementation defect. | Partially addressed. `run_summary.csv` now labels the attenuation model as `beer_lambert_primary_transmission` so the output is not mistaken for a buildup-corrected estimate. |
| 5 | `fLayerMaterials` can become stale/null between geometry rebuilds | Confirmed | `GetLayerMaterial()` could return `nullptr` when the geometry cache had been cleared and not repopulated yet. | Fixed. `GetLayerMaterial()` now lazily resolves and repopulates missing material pointers on demand. |
| 6 | `divisions` stored in `ShieldLayer` but ignored in geometry construction | Confirmed | The earlier review was correct: layer subdivisions were accepted but not used in geometry placement. | Fixed. Each layer is now segmented according to `divisions`, with segment copy numbers mapped back to logical layer totals for energy-deposition accounting. |
| 7 | World volume copy number set to `-1` | Confirmed | The world placement used a non-standard copy number of `-1`. | Fixed. The world copy number is now `0`. |
| 8 | `cmake_minimum_required(VERSION 3.16...3.27)` is unnecessarily capped | Confirmed | The upper cap could reject newer CMake versions without technical benefit. | Fixed. The project now declares `cmake_minimum_required(VERSION 3.16)`. |

## Remaining Scientific/Design Notes

- Primary-only transmission and reflection remain intentional output semantics. If total escaping gamma yields or secondary backscatter fractions are required, that should be implemented as a separate tally with different normalization.
- The Monte Carlo summary output is now better labelled, but it is still not a substitute for buildup-factor workflows. Use the analytical Python layer for buildup-aware shielding studies.
- The default source remains gamma at 662 keV for convenience, but Geant4 macro commands can override particle type and energy at runtime.