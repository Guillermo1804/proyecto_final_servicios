# Copia .env.example -> .env en los 7 microservicios (Epic 1 — ISSUE-104)
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$dirs = @('ms-auth','ms-periodos','ms-alumnos','ms-calificaciones','ms-asistencias','ms-notificaciones','ms-reportes')
foreach ($d in $dirs) {
    $src = Join-Path $root "$d\.env.example"
    $dst = Join-Path $root "$d\.env"
    if (-not (Test-Path $src)) { Write-Warning "Falta $src"; continue }
    Copy-Item $src $dst -Force
    Write-Host "OK $dst"
}
