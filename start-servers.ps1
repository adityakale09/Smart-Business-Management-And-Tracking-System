# Start Backend and Frontend Servers
# This script launches both servers in separate PowerShell windows

Write-Host "Starting Backend Server..." -ForegroundColor Green
$backendPythonPath = $null
if (Test-Path "$PSScriptRoot\backend\venv\Scripts\python.exe") {
    $backendPythonPath = "$PSScriptRoot\backend\venv\Scripts\python.exe"
} elseif (Test-Path "$PSScriptRoot\backend\.venv\Scripts\python.exe") {
    $backendPythonPath = "$PSScriptRoot\backend\.venv\Scripts\python.exe"
} else {
    Write-Host "Backend venv not found. Create it in backend\\venv (or backend\\.venv) first." -ForegroundColor Red
    exit 1
}
$backendCommand = "Set-Location -Path '$PSScriptRoot\\backend'; Write-Host 'Backend Server Starting...' -ForegroundColor Cyan; & '$backendPythonPath' -m uvicorn main:app --host 0.0.0.0 --port 8000; if (`$LASTEXITCODE -ne 0) { Write-Host 'Backend server exited with code ' `$LASTEXITCODE -ForegroundColor Red }"
Start-Process powershell -ArgumentList '-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $backendCommand

Write-Host "Starting Frontend Server..." -ForegroundColor Green
$frontendCommand = "Set-Location -Path '$PSScriptRoot\\frontend'; if (-not (Test-Path .\\node_modules)) { Write-Host 'node_modules not found. Running npm install...' -ForegroundColor Yellow; npm install }; Write-Host 'Frontend Server Starting...' -ForegroundColor Cyan; npm run dev -- --host --port 5173; if (`$LASTEXITCODE -ne 0) { Write-Host 'Frontend server exited with code ' `$LASTEXITCODE -ForegroundColor Red }"
Start-Process powershell -ArgumentList '-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $frontendCommand

# Detect likely LAN IPv4 (exclude loopback, virtual adapters, and link-local)
$lanIp = (
    Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object {
        $_.IPAddress -notlike '127.*' -and
        $_.IPAddress -notlike '169.254.*' -and
        $_.IPAddress -notlike '192.168.56.*' -and
        $_.IPAddress -notlike '192.168.74.*' -and
        $_.PrefixOrigin -ne 'WellKnown'
    } |
    Sort-Object -Property InterfaceMetric |
    Select-Object -ExpandProperty IPAddress -First 1
)

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
Write-Host "  http://localhost:5173" -ForegroundColor White
Write-Host "  http://localhost:5173/dashboard" -ForegroundColor White
if ($lanIp) {
    Write-Host "  http://$lanIp`:5173  (Use this on other devices in same network)" -ForegroundColor White
    Write-Host "  http://$lanIp`:5173/dashboard" -ForegroundColor White
}
Write-Host ""
Write-Host "Default Admin Credentials:" -ForegroundColor Magenta
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin123" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit this window (servers will continue running)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
