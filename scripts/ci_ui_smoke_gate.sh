#!/usr/bin/env bash
set -euo pipefail

# Release gate for UI smoke tests:
# - starts Streamlit app
# - runs Playwright-backed smoke tests
# - fails on pytest failures, skips, xfail/xpass, or zero test collection

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

: "${SHIELDLAB_PORT:=8501}"
: "${SHIELDLAB_BASE_URL:=http://127.0.0.1:${SHIELDLAB_PORT}}"

export SHIELDLAB_UI_SMOKE=1
export SHIELDLAB_BASE_URL
# Ensure the shieldlab package (python/) and UI modules (ui/) are importable
# regardless of the launch directory or installed-package state.
export PYTHONPATH="${ROOT_DIR}/python:${ROOT_DIR}/ui${PYTHONPATH:+:${PYTHONPATH}}"

SERVER_LOG="${ROOT_DIR}/.ci_streamlit.log"
rm -f "$SERVER_LOG"

echo "[ui-smoke] python: $(python --version 2>&1)"
echo "[ui-smoke] PYTHONPATH=$PYTHONPATH"
echo "[ui-smoke] launching Streamlit (ui/app.py) on port $SHIELDLAB_PORT"
python -m streamlit run ui/app.py --server.headless true --server.port "$SHIELDLAB_PORT" >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!

cleanup() {
  if kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# Wait for Streamlit to become reachable, failing fast if it dies on startup.
ready=0
for i in $(seq 1 90); do
  if curl -fsS "$SHIELDLAB_BASE_URL" >/dev/null 2>&1; then
    ready=1
    echo "[ui-smoke] Streamlit ready after ${i}s"
    break
  fi
  if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    echo "[ui-smoke] Streamlit process exited before becoming ready (after ${i}s)"
    break
  fi
  sleep 1
done

# Always surface the Streamlit startup log so CI failures are diagnosable.
echo "---- Streamlit startup log (begin) ----"
cat "$SERVER_LOG" 2>/dev/null || echo "(no streamlit log captured)"
echo "---- Streamlit startup log (end) ----"

if [ "$ready" -ne 1 ]; then
  echo "Release gate failed: Streamlit did not become ready at $SHIELDLAB_BASE_URL" >&2
  exit 1
fi

# Capture pytest output while preserving real exit behavior.
out="$(python -m pytest tests/test_ui_playwright_smoke.py -q -rA 2>&1)"
code=$?
printf '%s\n' "$out"

if [ "$code" -ne 0 ]; then
  echo "Release gate failed: UI smoke pytest failed with exit code $code" >&2
  echo "---- Streamlit log ----" >&2
  cat "$SERVER_LOG" >&2 || true
  exit "$code"
fi

if printf '%s' "$out" | grep -Eiq '(^|[^[:alpha:]])(skipped|xfailed|xpassed)([^[:alpha:]]|$)|collected[[:space:]]+0[[:space:]]+items|no tests ran'; then
  echo "Release gate failed: UI smoke tests did not execute cleanly with no skips/xfail/xpass and non-zero collection." >&2
  exit 1
fi

echo "Release gate passed: UI smoke executed with no skips and non-zero test collection."
