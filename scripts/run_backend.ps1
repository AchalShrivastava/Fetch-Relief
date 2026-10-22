# Fetch Relief: Launch FastAPI Backend Server
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting Fetch Relief Emergency Coordination API Backend  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$VenvPython = ".\venv\Scripts\python.exe"
if (-Not (Test-Path $VenvPython)) {
    Write-Warning "Virtual environment not detected at .\venv. Falling back to system python."
    $VenvPython = "python"
}

& $VenvPython -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
