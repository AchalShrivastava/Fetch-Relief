# Fetch Relief: Launch Fetch.ai uAgent with ACP Protocol
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Starting Fetch Relief Public uAgent (Agent Chat Protocol)  " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

$VenvPython = ".\venv\Scripts\python.exe"
if (-Not (Test-Path $VenvPython)) {
    Write-Warning "Virtual environment not detected at .\venv. Falling back to system python."
    $VenvPython = "python"
}

& $VenvPython -m agents.master_agent
