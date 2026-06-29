# Release Candidate Checklist Report

Date: 2026-05-06
Scope: startup checks, UI checks, export checks, known residuals
Mode: strict pass/fail evidence for sign-off

## 1. Startup Checks

1. Backup snapshot created: PASS
- Evidence: d:/projects/ShieldLabG4/backups/ShieldLabG4_backup_20260506_203344

2. Compile gate for RC-critical files: PASS
- Command outcome: no output, no syntax failures
- Files checked:
  - ui/app.py
  - ui/components/asset_integrity.py
  - ui/components/styles.py
  - ui/pages/shielding_calculator.py
  - ui/pages/results_explorer.py
  - python/shieldlab/io/descriptor_schema.py
  - python/shieldlab/viz/style.py
  - tests/test_ui_playwright_smoke.py

3. UI module import smoke: PASS
- Evidence:
  - SMOKE_START 12
  - TOTAL_FAIL 0
- Notes:
  - Non-fatal warnings observed in shielding math and comparison legend.

4. Problems panel diagnostics: PASS
- No errors found in:
  - ui/app.py
  - ui/components/styles.py
  - ui/pages/shielding_calculator.py
  - python/shieldlab/io/descriptor_schema.py

## 2. UI Checks

1. Multi-page crash scan (live browser): PASS
- Pages checked:
  - /
  - /study_builder
  - /run_study
  - /shielding_calculator
  - /comparison
  - /dose_rate
  - /results_explorer
  - /literature_benchmarks
  - /benchmark_dashboard
  - /methods
  - /about
  - /settings
- Evidence:
  - hasTraceback=false on all pages
  - hasValueError=false on all pages
  - hasTypeError=false on all pages
  - hasKeyError=false on all pages

2. Sidebar style refresh verification: PASS
- Evidence from computed styles:
  - scrollbarColor: rgba(26, 115, 217, 0.82) rgba(194, 220, 249, 0.62)
  - nav font-weight: 650
  - nav font-size: 15.04px
  - nav color: rgb(233, 242, 255)

3. Control geometry consistency (select/number): PASS
- Evidence from computed styles:
  - Select shells: uniform 40px height
  - Number inputs: 40px body and 40px stepper buttons

## 3. Export Checks

1. Descriptor schema mixed-type coercion: PASS
- Test payload included:
  - name='MyMaterial'
  - density=2.0
  - Zeff=13.2
  - enabled=True
  - nonev=None
- Evidence output:
  - ('name', 'str', 'MyMaterial')
  - ('density', 'float', 2.0)
  - ('Zeff', 'float', 13.2)
  - ('enabled', 'bool', True)
  - ('nonev', 'str', '')

2. Previous shielding export crash condition: PASS
- Runtime symptom previously reported:
  - ValueError: could not convert string to float: 'MyMaterial'
- Current live check on /shielding_calculator:
  - calculatorErrorVisible=false

## 4. Automation Checks

1. New UI smoke test file exists and is runnable: PASS
- File:
  - tests/test_ui_playwright_smoke.py
- Test run result:
  - ss
  - 2 skipped in 0.18s

2. Automated smoke fully executed in this environment: FAIL
- Reason:
  - Tests were skipped due environment/runtime dependency gating (Playwright runtime not available in this execution context).

## 5. Known Residuals

1. Recurrent browser console 404 events during navigation: FAIL (open)
- Impact:
  - Did not block page rendering in this pass.
- Recommendation:
  - Add startup/static asset integrity tracing and fix missing resource routes.

2. Non-fatal runtime warnings in physics/legend path: FAIL (open)
- Observed:
  - overflow encountered in shielding_params
  - legend warning in comparison page
- Impact:
  - No crash; import smoke still passes.

3. Full action-by-action click matrix for every conditional branch: FAIL (open)
- Current state:
  - Representative live checks done, but exhaustive branch coverage is not complete.
- Recommendation:
  - Expand deterministic fixtures for run-time states and gate on full click matrix.

## 6. Sign-off Decision

Decision: CONDITIONAL PASS

Rationale:
1. Startup/import/compile gates pass.
2. No page-level tracebacks in strict multi-page scan.
3. Export path regression that previously crashed is resolved.
4. Residuals are non-blocking for current RC but must be tracked for next hardening sprint.

Release condition note:
- Promote to full PASS after resolving console 404 residuals and running non-skipped Playwright smoke in CI.

## 7. CI No-Skip Gate (Release Blocking)

Reusable scripts committed:
- scripts/ci_ui_smoke_gate.sh
- scripts/ci_ui_smoke_gate.ps1

Workflow wiring committed:
- .github/workflows/release-validation-gate.yml now runs the bash gate on Ubuntu after installing UI smoke dependencies.

Use one of the following CI command blocks to enforce no-skip UI smoke execution.
The pipeline fails if tests are skipped, fail, error, xfail/xpass unexpectedly, or if zero tests are collected.

PowerShell (Windows agents):

```powershell
$env:SHIELDLAB_UI_SMOKE = "1"
$out = d:\uv_envs\Scripts\python.exe -m pytest tests\test_ui_playwright_smoke.py -q -rA 2>&1
$code = $LASTEXITCODE
$text = ($out | Out-String)

# Surface pytest output in CI logs.
$text

if ($code -ne 0) {
    Write-Error "UI smoke pytest failed with exit code $code"
    exit $code
}

# Release gate: fail if pytest reported skips, xfail/xpass, or collected zero tests.
if ($text -match "(?im)(\bskipped\b|\b xfailed\b|\b xpassed\b|collected\s+0\s+items|no tests ran)") {
    Write-Error "Release gate failed: UI smoke tests did not execute cleanly with no skips/xfail/xpass and non-zero collection."
    exit 1
}

Write-Host "Release gate passed: UI smoke executed with no skips and non-zero test collection."
```

Bash (Linux/macOS agents):

```bash
set -euo pipefail
export SHIELDLAB_UI_SMOKE=1

out="$(python -m pytest tests/test_ui_playwright_smoke.py -q -rA 2>&1)"
code=$?
printf '%s\n' "$out"

if [ "$code" -ne 0 ]; then
  echo "UI smoke pytest failed with exit code $code" >&2
  exit "$code"
fi

# Release gate: fail if pytest reported skips, xfail/xpass, or collected zero tests.
if printf '%s' "$out" | grep -Eiq '(^|[^[:alpha:]])(skipped|xfailed|xpassed)([^[:alpha:]]|$)|collected[[:space:]]+0[[:space:]]+items|no tests ran'; then
  echo "Release gate failed: UI smoke tests did not execute cleanly with no skips/xfail/xpass and non-zero collection." >&2
  exit 1
fi

echo "Release gate passed: UI smoke executed with no skips and non-zero test collection."
```
