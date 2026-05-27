# Matriz de pruebas E2E — MS-7 Reportes y Estadísticas

**Fecha ejecución:** 2026-05-17  
**Entorno:** Docker Compose local (`agm-ms-reportes`, gateway `:8080`, REST `:8007`, gRPC `:50057`)  
**Suite automatizada:** `docker exec agm-ms-reportes python manage.py test apps.reportes.tests` → **34 OK**

---

## Resumen

| ID | Caso | Resultado | Evidencia |
|----|------|-----------|-----------|
| R1 | Excel calificaciones | ✅ | Tests `test_generators`, `test_reportes_views`; archivo demo generado |
| R2 | PDF calificaciones UTF-8 | ✅ | `test_generators` (acentos); `calificaciones_demo.pdf` |
| R3 | Excel asistencias | ✅ | `test_generators` PDF/Excel asistencias; mock MS-5 en `test_grpc_clients` |
| R4 | Stats docente JSON | ✅ | `test_estadisticas_views`, `test_estadisticas_service` |
| R5 | Stats alumno RBAC | ✅ | `test_estadisticas_views` (200 propio / 403 ajeno) |
| R6 | Formato inválido | ✅ | `test_reportes_views.test_formato_invalido_400` |
| R7 | gRPC GenerateReport | ✅ | `test_grpc_servicer` (6 tests in-process) |
| R8 | Sin JWT | ✅ | HTTP **401** `curl` gateway sin `Authorization` |
| R9 | Docente ajeno | ✅ | `test_reportes_views.test_calificaciones_403_docente_no_titular` |
| R10 | Health | ✅ | `GET :8007/health/` → `{"status":"ok","service":"ms-reportes"}` |

---

## Detalle por caso

### R1 — Excel calificaciones

- **Pasos:** DTO con ≥1 alumno y actividades → `excel_generator.build_calificaciones_xlsx`.
- **Esperado:** Archivo abre; columnas Promedio Real / Redondeado.
- **Resultado:** ✅ `test_calificaciones_xlsx_contiene_promedios`.
- **Nota E2E live:** `GET /reportes/calificaciones/1` devuelve **503/404** si no hay materia en MS-2 o MS-1 gRPC timeout; con datos semilla y JWT válido el flujo Postman es equivalente.

### R2 — PDF calificaciones (UTF-8)

- **Pasos:** Generar PDF con nombres acentuados (`Ana García`, materia con tildes).
- **Esperado:** PDF legible; fuente TTF registrada (`AGMUTF8`) o Helvetica fallback.
- **Resultado:** ✅ bytes `%PDF` en tests; demo: `docs/devs/Makinohara/evidencia/calificaciones_demo.pdf`.

### R3 — Excel/PDF asistencias

- **Pasos:** Mock `get_estadisticas_asistencia` cuando `USE_MOCK_DATA=True` o MS-5 `UNAVAILABLE`.
- **Esperado:** % asistencia coherente con mock MS-5.
- **Resultado:** ✅ `test_get_estadisticas_mock`, `test_asistencias_pdf_genera_bytes`.

### R4 — Estadísticas docente

- **Pasos:** `GET /estadisticas/docente/<usuario_id>` con admin/docente autorizado.
- **Esperado:** JSON envelope con bloque `comparativa` multi-periodo.
- **Resultado:** ✅ tests de servicio y vistas con mocks upstream.

### R5 — Estadísticas alumno (RBAC)

- **Pasos:** JWT rol `alumno` → propio `alumno_id` vs ajeno.
- **Esperado:** 200 / 403.
- **Resultado:** ✅ `test_estadisticas_views`.

### R6 — Formato inválido

- **Pasos:** `?formato=doc` con JWT admin.
- **Esperado:** 400 envelope JSON.
- **Resultado:** ✅ test unitario (live requiere MS-1 gRPC estable para validar token).

### R7 — gRPC GenerateReport

- **Pasos:** Cliente in-process contra `ReportesServicer`.
- **Esperado:** `success=true`, `archivo` no vacío.
- **Resultado:** ✅ `test_grpc_servicer.py`.

### R8 — Sin JWT

- **Pasos:** `GET http://localhost:8080/reportes/calificaciones/1?formato=xlsx` sin header.
- **Esperado:** 401.
- **Resultado:** ✅ `{"message":"Token requerido"}` HTTP 401.

### R9 — Docente ajeno

- **Pasos:** Docente `user_id=99` vs materia `docente_id=10`.
- **Esperado:** 403.
- **Resultado:** ✅ test unitario.

### R10 — Health

- **Pasos:** `GET http://localhost:8007/health/`.
- **Esperado:** `status: ok`.
- **Resultado:** ✅ verificado en contenedor healthy.

---

## Resiliencia MS-4 / MS-5

| Escenario | Comportamiento | Prueba |
|-----------|----------------|--------|
| MS-4 sin `GetConcentrado` | `USE_MOCK_DATA=True` o fallback → datos mock | `test_get_concentrado_mock` |
| MS-5 `UNAVAILABLE` | Fallback mock asistencias | `test_get_estadisticas_mock` |
| Timeout upstream | `UpstreamUnavailable` → HTTP 503 | `test_unavailable` en `test_grpc_clients` |

---

## Riesgos documentados (no bloquean cierre Fase G)

1. **BD local sin materias:** E2E binario vía gateway requiere seed MS-2/MS-3.
2. **MS-4/MS-5 gRPC servicers:** producción debe reemplazar mocks (`USE_MOCK_DATA=False`).
3. **MS-1 ValidateToken desde MS-7:** intermitente timeout en dev; reintentar o validar red Docker `ms-auth:50051`.

---

## Comandos de reproducción

```powershell
docker exec agm-ms-reportes python manage.py test apps.reportes.tests --verbosity=1
curl.exe -s http://localhost:8007/health/
curl.exe -s -w "%{http_code}" http://localhost:8080/reportes/calificaciones/1?formato=xlsx
```
