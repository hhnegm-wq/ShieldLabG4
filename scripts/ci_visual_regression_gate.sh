#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

: "${SHIELDLAB_PORT:=8501}"
: "${SHIELDLAB_BASE_URL:=http://127.0.0.1:${SHIELDLAB_PORT}}"

export SHIELDLAB_UI_SMOKE=1
export SHIELDLAB_BASE_URL
export PYTHONPATH="${ROOT_DIR}/python:${ROOT_DIR}/ui${PYTHONPATH:+:${PYTHONPATH}}"

SERVER_LOG="${ROOT_DIR}/.ci_streamlit_visual.log"
rm -f "$SERVER_LOG"

echo "[visual-regression] python: $(python --version 2>&1)"
echo "[visual-regression] PYTHONPATH=$PYTHONPATH"
echo "[visual-regression] launching Streamlit (ui/app.py) on port $SHIELDLAB_PORT"
python -m streamlit run ui/app.py --server.headless true --server.port "$SHIELDLAB_PORT" >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!

cleanup() {
  if kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

ready=0
for i in $(seq 1 90); do
  if curl -fsS "$SHIELDLAB_BASE_URL" >/dev/null 2>&1; then
    ready=1
    echo "[visual-regression] Streamlit ready after ${i}s"
    break
  fi
  if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    echo "[visual-regression] Streamlit process exited before becoming ready (after ${i}s)"
    break
  fi
  sleep 1
done

echo "---- Streamlit startup log (begin) ----"
cat "$SERVER_LOG" 2>/dev/null || echo "(no streamlit log captured)"
echo "---- Streamlit startup log (end) ----"

if [ "$ready" -ne 1 ]; then
  echo "Visual gate failed: Streamlit did not become ready at $SHIELDLAB_BASE_URL" >&2
  exit 1
fi

set +e
out="$(python -m pytest tests/visual/test_visual_regression.py -q -rA 2>&1)"
code=$?
set -e
printf '%s\n' "$out"

if [ "$code" -ne 0 ]; then
  echo "Visual gate failed: visual regression pytest failed with exit code $code" >&2
  echo "---- Streamlit log ----" >&2
  cat "$SERVER_LOG" >&2 || true
  exit "$code"
fi

if printf '%s' "$out" | grep -Eiq '(^|[^[:alpha:]])(skipped|xfailed|xpassed)([^[:alpha:]]|$)|collected[[:space:]]+0[[:space:]]+items|no tests ran'; then
  echo "Visual gate failed: visual tests did not execute cleanly with no skips/xfail/xpass and non-zero collection." >&2
  exit 1
fi

echo "Visual gate passed: baseline screenshots match current UI."