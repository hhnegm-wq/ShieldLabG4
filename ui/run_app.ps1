# ShieldLab G4 – Launch Streamlit UI
$env:PYTHONPATH = '\\wsl.localhost\Ubuntu\home\negm_\geant4-install\ShieldLabG4\python'
$AppPath = Join-Path $PSScriptRoot 'app.py'
d:/uv_envs/Scripts/streamlit.exe run $AppPath --server.headless false --browser.gatherUsageStats false
