# Matriz de pruebas MS-6 (P1–P10)

**Fecha ejecución:** 2026-05-17  
**Entorno:** Docker Compose local (`agm-ms-notificaciones`, gateway `:8080`)  
**Suite automatizada:** `docker exec agm-ms-notificaciones python manage.py test apps.notificaciones.tests` → **20 tests OK**

---

| ID | Caso | Método / evidencia | Resultado | Estado |
|----|------|-------------------|-----------|--------|
| **P1** | Bienvenida gRPC | `test_grpc_servicer.NotificacionesGrpcServicerTests.test_send_bienvenida_ok` (locmem + PlaceholderDataProvider) | `success=True`, mensaje contiene envío | ✅ |
| **P2** | Alumno inexistente | `test_send_bienvenida_invalid_argument` (gRPC `INVALID_ARGUMENT`); dominio: `test_send_bienvenida_alumno_no_encontrado` | Código gRPC/HTTP acorde | ✅ |
| **P3** | Baja docente | `test_send_baja_ok` (servicio + gRPC servicer) | Correo registrado en historial | ✅ |
| **P4** | Cierre 0 alumnos | `PlaceholderDataProvider` materia inválida → mensaje sin crash; lógica en `EmailService.send_cierre_materia` | `enviados=0`, mensaje claro | ✅ |
| **P5** | Cierre ≥3 alumnos | `test_send_cierre_materia_multiple` + `test_send_cierre_materia_ok` (pool `EMAIL_MAX_WORKERS`) | Sin timeout en tests; N historiales | ✅ |
| **P6** | Reset password | `test_send_reset_password_ok` (REST + gRPC) | Plantilla con `reset_url` | ✅ |
| **P7** | SMTP caído | Servicio captura excepción SMTP → `HistorialCorreo.exitoso=False`; proceso no termina | `test_email_service` + logs en runtime con credencial inválida | ✅ |
| **P8** | REST sin API key | `test_bienvenida_requires_auth` + shell: `POST /notificaciones/bienvenida` sin header | **HTTP 401**, `success: false` | ✅ |
| **P9** | CORS preflight | `OPTIONS http://localhost:8006/notificaciones/bienvenida` + `Origin: http://localhost:4200` | **HTTP 200** | ✅ |
| **P10** | Health | `GET http://localhost:8006/health/` | **200** `{"status":"ok","service":"ms-notificaciones"}` | ✅ |

---

## Evidencias JSON (muestras)

### P8 — 401 sin API key

```json
{
  "success": false,
  "data": null,
  "message": "No autorizado: requiere X-Internal-Api-Key válida o JWT de administrador",
  "errors": {}
}
```

### P10 — Health

```json
{"status": "ok", "service": "ms-notificaciones"}
```

### P1 — Respuesta gRPC (tests)

```
SendBienvenida → success=True, message="Correo enviado"
```

---

## Demo §6.3 (correo real + historial)

1. Configurar SMTP real en `ms-notificaciones/.env` (`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`).
2. Ejecutar:  
   `docker exec agm-ms-notificaciones python manage.py send_test_email --to TU_CORREO@dominio.com`
3. Verificar bandeja de entrada.
4. Auditoría:
   - Django Admin: `http://localhost:8006/admin/` → **Historial correos**
   - O SQL: `SELECT tipo, destinatario_email, exitoso, enviado_en FROM notificaciones_historialcorreo ORDER BY id DESC LIMIT 5;`

**Nota:** No adjuntar capturas con contraseñas SMTP ni API keys en el repositorio.

---

## Integración E2E (Fase F)

| Escenario | Verificación |
|-----------|----------------|
| MS-3 import → bienvenida | `utils/notificaciones_client.py` + `auth_client.CreateUser` |
| MS-3 baja | `docente_id` vía MS-2 `GetMateriaById` |
| MS-4 cerrar | `POST /calificaciones/materias/{id}/cerrar` → `SendCierreMateria` |
| MS-1 forgot-password | `grpc_clients.send_reset_password_notification` |
| MS-6 caído | Import/cierre no abortan; log `warning` |

---

## Issues backlog

ISSUE-801 … **806**: ver `docs/backlog_AGM_completo.md` (Epic 8 marcada completada).
