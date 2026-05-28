# Pruebas frontend ↔ MS-7 (Reportes y estadísticas)

## Proyecciones MS-7 (importante)

MS-7 construye estadísticas y reportes desde su **read model local** (`ReporteMateriaProjection`, etc.). Si el dashboard sale vacío pero MS-2/3/4 tienen datos:

```bash
# Sincroniza materias/inscripciones desde las BD de MS-2 y MS-3 (requiere BACKFILL_* en ms-reportes/.env)
docker compose exec ms-reportes python manage.py rebuild_report_projections --from-backfill

# Solo demo (docente_id=1, materia_id=1) — no usa tus datos reales del docente 176
# docker compose exec ms-reportes python manage.py rebuild_report_projections
```

Reinicia el consumer si cambiaste código:

```bash
docker compose restart ms-reportes-worker-consumer
```

Ver también `docs/CONSISTENCIA_PROYECCIONES.md`.

## Infraestructura

Levantar al menos MS-1, MS-2, MS-3, MS-4, MS-5, **MS-7**, Redis y Nginx:

```bash
docker compose up -d ms-auth ms-periodos ms-alumnos ms-calificaciones ms-asistencias ms-reportes redis nginx
```

Tras cambiar `docker/nginx/default.conf` o `proxy.conf.json`, recrear nginx y reiniciar `ng serve`:

```bash
docker compose up -d --force-recreate nginx
cd frontend/sistema_AGM && npm start
```

## Pantalla docente (`/docente/reportes`)

1. Login docente (`quecholacdavid11+docente@gmail.com` / contraseña de prueba).
2. La pantalla llama `GET /estadisticas/docente/{usuario_id}` (JWT del docente; solo su propio `usuario_id`).
3. Métricas, historial y comparativas vienen de MS-7 si hay proyecciones; si no, fallback a concentrado MS-4.
4. **Exportar acta:** elegir materia y tipo → `GET /reportes/calificaciones/{materia_id}?formato=pdf|xlsx`.
5. **Exportar asistencias:** tipo Asistencias → `GET /reportes/asistencias/{materia_id}?formato=pdf|xlsx`.
6. El historial de exportaciones se guarda en `sessionStorage` del navegador (esta sesión).

## Asistencias (misma API MS-7)

En `/docente/asistencias`, el enlace «Ver reportes» lleva a `/docente/reportes`. La descarga MS-7 de asistencias también está disponible desde la pantalla de reportes.

## Rutas proxy (Angular → Nginx → MS-7)

| Prefijo | Backend |
|---------|---------|
| `/reportes/` | `ms-reportes:8007` |
| `/estadisticas/` | `ms-reportes:8007` |

## Comprobación rápida con curl

```bash
TOKEN="<access_token_docente>"
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8080/estadisticas/docente/176 | head
curl -s -o /tmp/acta.pdf -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:8080/reportes/calificaciones/1?formato=pdf"
```

## Errores frecuentes

| Síntoma | Causa probable |
|---------|----------------|
| 403 en estadísticas | `usuario_id` de la URL distinto al del JWT |
| 403 en reporte | Docente no titular de la materia en proyección MS-7 |
| 404 sin datos | Sin calificaciones/asistencias proyectadas para esa materia |
| Dashboard vacío | Falta `rebuild_report_projections --from-backfill` o consumer detenido |
