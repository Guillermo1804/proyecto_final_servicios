# Levanta el stack COMPLETO (MS-1…7 + workers + gateway con frontend).
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Inicia Docker Desktop primero." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "ms-auth\.env")) {
    if (Test-Path "scripts\copy-env.ps1") {
        & "$PSScriptRoot\copy-env.ps1"
    } else {
        Write-Host "Copia ms-*/.env desde .env.example antes de continuar." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Levantando stack completo AGM (puede tardar varios minutos la primera vez)..." -ForegroundColor Cyan
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

Write-Host ""
Write-Host "Listo. Abre http://localhost:8080 (frontend + API)." -ForegroundColor Green
Write-Host "Health: http://localhost:8080/health" -ForegroundColor Green
Write-Host "Logs: docker compose logs -f nginx" -ForegroundColor Gray
