# Carga datos demo en todos los MS (idempotente). Requiere stack Docker levantado.
# Uso: .\scripts\seed-demo.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== AGM Seed demo completo ===" -ForegroundColor Cyan

function Parse-SeedLine {
    param(
        [string[]]$Lines,
        [string]$Key
    )
    $prefix = $Key + "="
    foreach ($line in $Lines) {
        if ($line -and $line.StartsWith($prefix)) {
            return $line.Substring($prefix.Length).Trim()
        }
    }
    throw "No se encontro $Key en la salida del seed."
}

Write-Host ""
Write-Host "[1/5] MS-1 Auth - usuarios..." -ForegroundColor Yellow
$authOut = @(docker exec agm-ms-auth python manage.py seed_demo_users 2>&1)
$authOut | ForEach-Object { Write-Host $_ }
$docenteUid = Parse-SeedLine -Lines $authOut -Key "SEED_DOCENTE_USUARIO_ID"
$alumnoUid = Parse-SeedLine -Lines $authOut -Key "SEED_ALUMNO_USUARIO_ID"
$alumno2Uid = Parse-SeedLine -Lines $authOut -Key "SEED_ALUMNO2_USUARIO_ID"
$alumno3Uid = Parse-SeedLine -Lines $authOut -Key "SEED_ALUMNO3_USUARIO_ID"

Write-Host ""
Write-Host "[2/5] MS-2 Periodos - materias..." -ForegroundColor Yellow
$perOut = @(docker exec agm-ms-periodos python manage.py seed_demo --docente-usuario-id=$docenteUid 2>&1)
$perOut | ForEach-Object { Write-Host $_ }
$materiaIds = Parse-SeedLine -Lines $perOut -Key "SEED_MATERIA_IDS"

Write-Host ""
Write-Host "[3/5] MS-3 Alumnos - inscripciones..." -ForegroundColor Yellow
$alOut = @(docker exec agm-ms-alumnos python manage.py seed_demo --docente-usuario-id=$docenteUid --alumno-usuario-id=$alumnoUid --alumno2-usuario-id=$alumno2Uid --alumno3-usuario-id=$alumno3Uid --materia-ids=$materiaIds 2>&1)
$alOut | ForEach-Object { Write-Host $_ }
$alumnoMs3Ids = Parse-SeedLine -Lines $alOut -Key "SEED_ALUMNO_MS3_IDS"

Write-Host ""
Write-Host "[4/5] MS-4 Calificaciones..." -ForegroundColor Yellow
@(docker exec agm-ms-calificaciones python manage.py seed_demo --materia-ids=$materiaIds --alumno-ids=$alumnoMs3Ids 2>&1) | ForEach-Object { Write-Host $_ }

Write-Host ""
Write-Host "[5/5] MS-5 Asistencias..." -ForegroundColor Yellow
$firstMateria = ($materiaIds -split ",")[0]
@(docker exec agm-ms-asistencias python manage.py seed_demo --materia-id=$firstMateria --docente-usuario-id=$docenteUid --alumno-ids=$alumnoMs3Ids 2>&1) | ForEach-Object { Write-Host $_ }

Write-Host ""
Write-Host "Reiniciando gateway (evita 502 si se recrearon contenedores)..." -ForegroundColor Yellow
docker compose restart nginx | Out-Null
Start-Sleep -Seconds 4

Write-Host ""
Write-Host "=== LISTO ===" -ForegroundColor Green
Write-Host "Login: http://localhost:4200/login"
Write-Host "  admin@agm.buap.mx / admin123"
Write-Host "  docente.demo@agm.buap.mx / Docente123!"
Write-Host "  alumno.demo@agm.buap.mx / Alumno123!"
Write-Host "Gateway API: http://localhost:8080"
Write-Host "Ver docs/DEMO_DATOS.md"
