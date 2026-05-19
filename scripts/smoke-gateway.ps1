# Smoke test del API Gateway AGM (Epic 1 — ISSUE-107)
$base = if ($env:AGM_GATEWAY_URL) { $env:AGM_GATEWAY_URL } else { 'http://localhost:8080' }
$paths = @(
    '/health',
    '/auth/login',
    '/periodos/',
    '/materias/',
    '/docentes/',
    '/alumnos/',
    '/ponderaciones/',
    '/actividades/',
    '/calificaciones/',
    '/sesiones/',
    '/qr/',
    '/registros/',
    '/asistencias/',
    '/estadisticas/',
    '/notificaciones/',
    '/reportes/'
)
$ok = 0
foreach ($p in $paths) {
    try {
        $r = Invoke-WebRequest -Uri "$base$p" -Method GET -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        $code = $r.StatusCode
    } catch {
        if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode } else { $code = 0 }
    }
    $status = if ($code -ge 200 -and $code -lt 500) { 'OK'; $ok++ } else { 'FAIL' }
    Write-Host ("{0,-22} {1} -> {2}" -f $p, $code, $status)
}
Write-Host "`nRutas respondiendo (2xx-4xx): $ok / $($paths.Count)"
if ($ok -lt $paths.Count) { exit 1 }
