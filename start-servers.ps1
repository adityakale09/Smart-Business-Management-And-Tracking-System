# Start Backend and Frontend Servers
# This script launches both servers in separate PowerShell windows

Write-Host "Starting Backend Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList '-NoExit', '-Command', 
    "cd '$PSScriptRoot\backend'; .\venv\Scripts\activate; Write-Host 'Backend Server Starting...' -ForegroundColor Cyan; uvicorn main:app --host 0.0.0.0 --port 8000"

Write-Host "Starting Frontend Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList '-NoExit', '-Command',
    "cd '$PSScriptRoot\frontend'; Write-Host 'Frontend Server Starting...' -ForegroundColor Cyan; npm run dev -- --host"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Yellow
Write-Host "Both servers are launching in separate windows..." -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Backend API will be available at:" -ForegroundColor Cyan
Write-Host "  http://localhost:8000" -ForegroundColor White
Write-Host "  http://localhost:8000/docs (API Documentation)" -ForegroundColor White
Write-Host ""
Write-Host "Frontend will be available at:" -ForegroundColor Cyan
Write-Host "  http://localhost:3000" -ForegroundColor White
Write-Host "  http://localhost:3000/dashboard" -ForegroundColor White
Write-Host ""
Write-Host "Default Admin Credentials:" -ForegroundColor Magenta
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin123" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit this window (servers will continue running)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
