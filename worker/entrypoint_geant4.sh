#!/usr/bin/env bash
set -euo pipefail

source /opt/geant4/bin/geant4.sh

dataset_status="$(geant4-config --check-datasets || true)"
if printf '%s\n' "$dataset_status" | grep -q 'NOTFOUND'; then
  geant4-config --install-datasets
  source /opt/geant4/bin/geant4.sh
fi

exec "$@"