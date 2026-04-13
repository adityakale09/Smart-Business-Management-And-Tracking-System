# One-click Docker stop script for this project

param(
    [switch]$WithVolumes
)

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

Write-Host "Stopping Docker services..." -ForegroundColor Yellow
Ensure-DockerAvailable

Set-Location $PSScriptRoot
if ($WithVolumes) {
    docker compose down -v
} else {
    docker compose down
}

Write-Host "Done." -ForegroundColor Green
