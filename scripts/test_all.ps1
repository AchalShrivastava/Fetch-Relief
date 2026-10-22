# Fetch Relief: Execute Comprehensive Automated Test Suite
Write-Host "==========================================================" -ForegroundColor Magenta
Write-Host "       Running Fetch Relief Automated Acceptance Tests      " -ForegroundColor Magenta
Write-Host "==========================================================" -ForegroundColor Magenta

$VenvPython = ".\venv\Scripts\python.exe"
if (-Not (Test-Path $VenvPython)) {
    $VenvPython = "python"
}

& $VenvPython -m pytest -v --tb=short
