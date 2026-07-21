#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# ShieldLab G4 — WSL / Linux Geant4 bootstrap
#
# Builds the Geant4 Monte Carlo core (app/, src/, include/) into build/ShieldLabG4.
# Geant4 is NOT built on native Windows; run this inside WSL (or any Linux) with
# a Geant4 11.x installation available.
#
# Usage:
#   bash scripts/bootstrap_wsl_geant4.sh
#
# Environment overrides:
#   GEANT4_ENV   Path to a Geant4 environment script to source
#                (e.g. ~/geant4-install/bin/geant4.sh). If unset, the script
#                tries common locations and falls back to whatever is on PATH.
#   BUILD_DIR    Build directory (default: build)
#   JOBS         Parallel build jobs (default: nproc)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BUILD_DIR="${BUILD_DIR:-build}"
JOBS="${JOBS:-$(nproc 2>/dev/null || echo 4)}"

echo "==> ShieldLab G4 Geant4 bootstrap"
echo "    repo:   $ROOT_DIR"
echo "    build:  $BUILD_DIR  (jobs: $JOBS)"

# 1. Source a Geant4 environment if provided or discoverable.
source_geant4() {
  if [ -n "${GEANT4_ENV:-}" ] && [ -f "$GEANT4_ENV" ]; then
    echo "==> Sourcing Geant4 env: $GEANT4_ENV"
    # shellcheck disable=SC1090
    source "$GEANT4_ENV"
    return 0
  fi
  for cand in \
    "$HOME/geant4-install/bin/geant4.sh" \
    "$HOME/geant4/install/bin/geant4.sh" \
    "/opt/geant4/bin/geant4.sh" \
    "/usr/local/bin/geant4.sh"; do
    if [ -f "$cand" ]; then
      echo "==> Sourcing Geant4 env: $cand"
      # shellcheck disable=SC1090
      source "$cand"
      return 0
    fi
  done
  echo "==> No geant4.sh found; relying on PATH / CMake package discovery."
}
source_geant4

# 2. Verify prerequisites.
command -v cmake >/dev/null 2>&1 || { echo "ERROR: cmake not found." >&2; exit 1; }
if ! command -v geant4-config >/dev/null 2>&1; then
  echo "WARNING: geant4-config not on PATH. If CMake cannot find Geant4, set" >&2
  echo "         GEANT4_ENV to your Geant4 install's bin/geant4.sh and re-run." >&2
fi

# 3. Configure + build.
echo "==> Configuring (cmake)"
cmake -S . -B "$BUILD_DIR"
echo "==> Building (cmake --build, -j $JOBS)"
cmake --build "$BUILD_DIR" -j "$JOBS"

# 4. Verify the binary.
BIN="$BUILD_DIR/ShieldLabG4"
if [ -x "$BIN" ]; then
  echo "==> SUCCESS: built $BIN"
  "$BIN" --help 2>/dev/null | head -n 20 || true
else
  echo "ERROR: expected binary not found at $BIN" >&2
  exit 1
fi
