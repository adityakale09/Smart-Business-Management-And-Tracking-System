# One-click Docker logs script for this project

param(
    [string]$Service = '',
    [int]$Tail = 200,
    [switch]$NoFollow
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

Ensure-DockerAvailable
Set-Location $PSScriptRoot

$args = @('compose', 'logs', '--tail', $Tail)
if (-not $NoFollow) {
    $args += '-f'
}
if ($Service) {
    $args += $Service
}

Write-Host "Showing Docker logs..." -ForegroundColor Green
& docker @args
