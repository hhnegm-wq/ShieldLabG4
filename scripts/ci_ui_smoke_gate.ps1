$ErrorActionPreference = "Stop"

# Release gate for UI smoke tests:
# - starts Streamlit app
# - runs Playwright-backed smoke tests
# - fails on pytest failures, skips, xfail/xpass, or zero test collection

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not $env:SHIELDLAB_PORT) {
    $env:SHIELDLAB_PORT = "8501"
}
if (-not $env:SHIELDLAB_BASE_URL) {
    $env:SHIELDLAB_BASE_URL = "http://127.0.0.1:$($env:SHIELDLAB_PORT)"
}
$env:SHIELDLAB_UI_SMOKE = "1"

$serverLog = Join-Path $root ".ci_streamlit.log"
if (Test-Path $serverLog) {
    Remove-Item $serverLog -Force
}

$proc = Start-Process -FilePath "python" -ArgumentList @(
    "-m", "streamlit", "run", "ui/app.py", "--server.headless", "true", "--server.port", $env:SHIELDLAB_PORT
) -NoNewWindow -RedirectStandardOutput $serverLog -RedirectStandardError $serverLog -PassThru

try {
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $env:SHIELDLAB_BASE_URL -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                $ready = $true
                break
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }

    if (-not $ready) {
        Write-Error "Release gate failed: Streamlit server did not become ready at $($env:SHIELDLAB_BASE_URL)"
        if (Test-Path $serverLog) {
            Write-Host "---- Streamlit log ----"
            Get-Content $serverLog
        }
        exit 1
    }

    $out = & python -m pytest tests/test_ui_playwright_smoke.py -q -rA 2>&1
    $code = $LASTEXITCODE
    $text = ($out | Out-String)
    $text

    if ($code -ne 0) {
        Write-Error "Release gate failed: UI smoke pytest failed with exit code $code"
        exit $code
    }

    if ($text -match "(?im)(\bskipped\b|\bxfailed\b|\bxpassed\b|collected\s+0\s+items|no tests ran)") {
        Write-Error "Release gate failed: UI smoke tests did not execute cleanly with no skips/xfail/xpass and non-zero collection."
        exit 1
    }

    Write-Host "Release gate passed: UI smoke executed with no skips and non-zero test collection."
}
finally {
    if ($proc -and -not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force
    }
}
