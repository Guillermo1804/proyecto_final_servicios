# Borra datos de MS-1…MS-4 (volumenes MySQL) y deja solo el admin en MS-1 al volver a levantar.
# No toca MS-5/6/7 ni RabbitMQ.
$ErrorActionPreference = "Continue"
$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

$Compose = @("-f", "docker-compose.yml", "-f", "docker-compose.ms1-4.yml")

$stopServices = @(
    "nginx",
    "ms-calificaciones-worker-consumer", "ms-calificaciones-worker-outbox", "ms-calificaciones",
    "ms-alumnos-worker-consumer", "ms-alumnos-outbox-worker", "ms-alumnos",
    "ms-periodos-worker-consumer", "ms-periodos-outbox-worker", "ms-periodos",
    "ms-auth-event-consumer", "ms-auth-outbox-worker", "ms-auth",
    "db-calificaciones", "db-alumnos", "db-periodos", "db-auth"
)

Write-Host "Deteniendo servicios MS-1…4..." -ForegroundColor Cyan
docker compose @Compose stop @stopServices 2>$null

$dbContainers = @("db-auth", "db-periodos", "db-alumnos", "db-calificaciones")
Write-Host "Eliminando contenedores de BD..." -ForegroundColor Cyan
docker compose @Compose rm -sf @dbContainers 2>$null

Write-Host "Eliminando volumenes MySQL (auth, periodos, alumnos, calificaciones)..." -ForegroundColor Cyan
$volumes = docker volume ls --format "{{.Name}}" | Where-Object {
    $_ -match "db_(auth|periodos|alumnos|calificaciones)_data$"
}
if (-not $volumes) {
    Write-Host "  No hay volumenes MS-1…4 que borrar." -ForegroundColor DarkYellow
} else {
    foreach ($vol in $volumes) {
        docker volume rm $vol 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK: $vol" -ForegroundColor Green
        } else {
            Write-Host "  (omitido: $vol)" -ForegroundColor DarkYellow
        }
    }
}

Write-Host "`nListo. Ejecuta: .\scripts\start-ms1-4-stack.ps1" -ForegroundColor Green
Write-Host "Admin (tras arranque): admin@agm.buap.mx / admin123 (ms-auth/.env)" -ForegroundColor Cyan
