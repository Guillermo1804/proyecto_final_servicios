# Levanta infra + MS-1…4 (API + workers event bus) + Nginx para el frontend (proxy :8080).
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Inicia Docker Desktop primero." -ForegroundColor Red
    exit 1
}

$Compose = @("-f", "docker-compose.yml", "-f", "docker-compose.ms1-4.yml")

function Wait-Healthy($name, $maxSec = 120) {
    $deadline = (Get-Date).AddSeconds($maxSec)
    while ((Get-Date) -lt $deadline) {
        $h = docker inspect --format "{{.State.Health.Status}}" $name 2>$null
        if ($h -eq "healthy") { return $true }
        if ($h -eq "unhealthy") { return $false }
        Start-Sleep -Seconds 3
    }
    return $false
}

Write-Host "1/4 Infra: RabbitMQ + MySQL MS-1…4" -ForegroundColor Cyan
docker compose @Compose up -d rabbitmq db-auth db-periodos db-alumnos db-calificaciones
foreach ($db in @("agm-db-auth", "agm-db-periodos", "agm-db-alumnos", "agm-db-calificaciones")) {
    if (-not (Wait-Healthy $db)) {
        Write-Host "BD no healthy: $db" -ForegroundColor Red
        exit 1
    }
}

Write-Host "2/4 MS-1 Auth (migraciones)" -ForegroundColor Cyan
docker compose @Compose up -d ms-auth
if (-not (Wait-Healthy "agm-ms-auth" 180)) {
    Write-Host "ms-auth no arranco. Logs:" -ForegroundColor Red
    docker logs agm-ms-auth --tail 40
    exit 1
}

Write-Host "3/4 MS-2, MS-3, MS-4 + workers" -ForegroundColor Cyan
docker compose @Compose up -d `
    ms-auth-outbox-worker, ms-auth-event-consumer `
    ms-periodos, ms-periodos-outbox-worker, ms-periodos-worker-consumer `
    ms-alumnos, ms-alumnos-outbox-worker, ms-alumnos-worker-consumer `
    ms-calificaciones, ms-calificaciones-worker-outbox, ms-calificaciones-worker-consumer

foreach ($c in @(
    "agm-ms-periodos", "agm-ms-alumnos", "agm-ms-calificaciones"
)) {
    if (-not (Wait-Healthy $c 180)) {
        Write-Host "No healthy: $c" -ForegroundColor Red
        docker logs $c --tail 30
        exit 1
    }
}

Write-Host "4/4 Nginx gateway" -ForegroundColor Cyan
docker compose @Compose up -d nginx
Start-Sleep -Seconds 3

Write-Host "`n========== LISTO ==========" -ForegroundColor Green
Write-Host "API Gateway:  http://localhost:8080"
Write-Host "MS-1 Auth:    http://localhost:8001/health/"
Write-Host "Login admin:  admin@agm.buap.mx / admin123"
Write-Host "`nFrontend (otra terminal):"
Write-Host "  cd frontend\sistema_AGM"
Write-Host "  npm start"
Write-Host "  -> http://localhost:4200 (proxy a Nginx :8080)"
