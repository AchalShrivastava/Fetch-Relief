# Fetch Relief: Reset Demo Data
Write-Host "Resetting Fetch Relief demo data to default baseline..." -ForegroundColor Yellow

$VenvPython = ".\venv\Scripts\python.exe"
if (-Not (Test-Path $VenvPython)) {
    $VenvPython = "python"
}

& $VenvPython .\scripts\reset_demo.py
