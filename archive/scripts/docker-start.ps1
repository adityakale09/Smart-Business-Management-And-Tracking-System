# One-click Docker start script for this project

$ErrorActionPreference = 'Stop'

function Ensure-DockerAvailable {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        return
    }

    $dockerBin = 'C:\Program Files\Docker\Docker\resources\bin'
    if (Test-Path (Join-Path $dockerBin 'docker.exe')) {
        $env:PATH = "$dockerBin;$env:PATH"
    }

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker CLI not found. Start Docker Desktop and reopen terminal."
    }
}

function Ensure-DockerDaemonRunning {
    # External commands do not throw in PowerShell by default, so check exit code explicitly.
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & docker info *> $null
    } finally {
        $ErrorActionPreference = $previousErrorAction
    }

    if ($LASTEXITCODE -eq 0) {
        return
    }

    $desktopExe = 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
    if (Test-Path $desktopExe) {
        Write-Host "Docker Desktop is not running. Launching Docker Desktop..." -ForegroundColor Yellow
        Start-Process -FilePath $desktopExe | Out-Null
    }

    Write-Host "Waiting for Docker engine to start (up to 90s)..." -ForegroundColor Yellow
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 3
        $previousErrorAction = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            & docker info *> $null
        } finally {
            $ErrorActionPreference = $previousErrorAction
        }
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Docker engine is ready." -ForegroundColor Green
            return
        }
    }

    throw "Docker daemon is not running. Open Docker Desktop and wait until it shows 'Engine running', then run this script again."
}

function Invoke-DockerOrThrow {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    & docker @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Docker command failed: docker $($Args -join ' ')"
    }
}

Write-Host "Starting Docker services..." -ForegroundColor Green
Ensure-DockerAvailable
Ensure-DockerDaemonRunning

Set-Location $PSScriptRoot
Invoke-DockerOrThrow -Args @('compose', 'up', '-d')

Write-Host "" 
Write-Host "Current container status:" -ForegroundColor Cyan
Invoke-DockerOrThrow -Args @('compose', 'ps')

Write-Host "" 
Write-Host "App URLs:" -ForegroundColor Yellow
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  Docs:     http://localhost:8000/docs" -ForegroundColor White
