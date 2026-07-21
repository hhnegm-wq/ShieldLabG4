# ShieldLab G4 — developer task runner
# Works on Linux / WSL (where the Geant4 toolchain lives). On Windows, run the
# Python targets from an activated environment or use WSL for the C++ targets.
#
# Usage:  make help
.DEFAULT_GOAL := help

# Repo-relative Python path so `shieldlab` (python/) and UI modules (ui/) import.
export PYTHONPATH := python:ui
PY  ?= python
PIP ?= $(PY) -m pip
PORT_UI  ?= 8501
PORT_API ?= 8000
BUILD_DIR ?= build

# Fast test selection (skips Geant4 binary, network, browser-UI, publication gates)
FAST_MARK := not geant4 and not publication and not ui and not network

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

## ── Python stack ────────────────────────────────────────────────────────────
.PHONY: install
install: ## Install the Python package (editable) + API deps + dev tools
	$(PIP) install --upgrade pip "setuptools>=83.0.0" wheel
	$(PIP) install -e ./python
	$(PIP) install -r api/requirements.txt
	$(PIP) install pytest ruff pre-commit pip-audit

.PHONY: test
test: ## Run the fast test suite (no Geant4/network/UI/publication)
	$(PY) -m pytest -q --ignore=backups -m "$(FAST_MARK)"

.PHONY: test-all
test-all: ## Run the full test suite (requires SHIELDLAB_TEST_GEANT4=1 for MC tests)
	$(PY) -m pytest -q --ignore=backups

.PHONY: lint
lint: ## Lint with ruff + run the project guards
	$(PY) -m ruff check python ui api cli tools
	$(PY) tools/deprecation_guard.py
	$(PY) tools/figure_audit.py --src-only --src-roots python/shieldlab ui

.PHONY: format
format: ## Auto-format with ruff
	$(PY) -m ruff format python ui api cli tools
	$(PY) -m ruff check --fix python ui api cli tools

.PHONY: audit
audit: ## Security-audit Python dependencies (pip-audit)
	$(PY) -m pip_audit

.PHONY: precommit
precommit: ## Run all pre-commit hooks across the repo
	pre-commit run --all-files

## ── Services ────────────────────────────────────────────────────────────────
.PHONY: ui
ui: ## Run the Streamlit UI
	$(PY) -m streamlit run ui/app.py --server.port $(PORT_UI)

.PHONY: api
api: ## Run the FastAPI service
	$(PY) -m uvicorn api.main:app --port $(PORT_API) --reload

## ── Geant4 C++ core (WSL / Linux) ───────────────────────────────────────────
.PHONY: build
build: ## Configure + build the Geant4 app (run inside WSL with Geant4 sourced)
	cmake -S . -B $(BUILD_DIR)
	cmake --build $(BUILD_DIR) -j

.PHONY: bootstrap-geant4
bootstrap-geant4: ## Guided WSL Geant4 build (see scripts/bootstrap_wsl_geant4.sh)
	bash scripts/bootstrap_wsl_geant4.sh

## ── Housekeeping ────────────────────────────────────────────────────────────
.PHONY: clean
clean: ## Remove Python caches and build artifacts
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .benchmarks *.egg-info python/*.egg-info
