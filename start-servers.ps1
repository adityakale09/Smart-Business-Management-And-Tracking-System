# Start Backend and Frontend Servers
# This script launches both servers in separate PowerShell windows

Write-Host "Starting Backend Server..." -ForegroundColor Green
$backendCommand = @'
if (-not (Test-Path .\venv\Scripts\Activate.ps1)) {
    Write-Host "Backend venv not found. Create it in backend\\venv first." -ForegroundColor Red
    exit 1
}
. .\venv\Scripts\Activate.ps1
Write-Host "Backend Server Starting..." -ForegroundColor Cyan
uvicorn main:app --host 0.0.0.0 --port 8000
'@
Start-Process powershell -WorkingDirectory "$PSScriptRoot\backend" -ArgumentList '-NoExit', '-Command', $backendCommand

Write-Host "Starting Frontend Server..." -ForegroundColor Green
$frontendCommand = @'
if (-not (Test-Path .\node_modules)) {
    Write-Host "node_modules not found. Running npm install..." -ForegroundColor Yellow
    npm install
}
Write-Host "Frontend Server Starting..." -ForegroundColor Cyan
npm run dev -- --host
'@
Start-Process powershell -WorkingDirectory "$PSScriptRoot\frontend" -ArgumentList '-NoExit', '-Command', $frontendCommand

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
Write-Host "  http://localhost:3000" -ForegroundColor White
Write-Host "  http://localhost:3000/dashboard" -ForegroundColor White
if ($lanIp) {
    Write-Host "  http://$lanIp`:3000  (Use this on other devices in same network)" -ForegroundColor White
    Write-Host "  http://$lanIp`:3000/dashboard" -ForegroundColor White
}
Write-Host ""
Write-Host "Default Admin Credentials:" -ForegroundColor Magenta
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin123" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit this window (servers will continue running)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
