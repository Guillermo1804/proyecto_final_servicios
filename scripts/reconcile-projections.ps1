# Reconciliación de read models (proyecciones) tras reset de BD, import masivo o drift del bus.
# Idempotente: solo upsert desde MS-2/MS-3; no altera flujos REST ni gRPC en caliente.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

Write-Host "Reconciliando proyecciones MS-3, MS-4, MS-5..." -ForegroundColor Cyan

# MS-3: reconcile_projections existe tras rebuild; si no, sync_materia_projections
docker compose exec ms-alumnos python manage.py sync_materia_projections 2>$null
if ($LASTEXITCODE -ne 0) {
  docker compose exec ms-alumnos python manage.py reconcile_projections
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

docker compose exec ms-calificaciones python manage.py reconcile_projections
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

docker compose exec ms-asistencias python manage.py reconcile_projections
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Listo. Los consumers del bus siguen siendo la via principal en operacion normal." -ForegroundColor Green
