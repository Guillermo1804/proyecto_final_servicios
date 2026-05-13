# Plan de acción — MS-6 Notificaciones (Epic 8)

**Desarrollador:** Makinohara  
**Microservicio:** MS-6 — Notificaciones  
**Carpeta:** `/ms-notificaciones/`  
**REST:** `8006` · **gRPC:** `50056` · **BD:** MySQL `agm_notificaciones_db`  
**Backlog:** `docs/backlog_AGM_completo.md` — **ISSUE-801 … ISSUE-806**  
**Enunciado:** `docs/Proyecto_Final_SW_AGM.md` — §5.2 (notificaciones por correo), §5.3 **Módulo 7**, §5.4.1 fila MS-6  
**Contexto:** `docs/CONTEXTO_GLOBAL_PROYECTO.md` §4 (tabla MS), §5 (lladas gRPC entrantes/salientes)  
**Especificación:** `docs/microservicios/MS6_NOTIFICACIONES.md`  
**Contrato:** `proto/notificaciones.proto`

---

## 1. Rol del MS-6 en el sistema AGM

MS-6 es el **único** responsable del envío de **correos transaccionales**. No calcula calificaciones ni guarda alumnos: **solo** compone mensajes, envía por SMTP y audita en `HistorialCorreo`. Los datos de negocio (nombre de alumno, correo, materia, lista de inscritos) llegan por **gRPC desde MS-2 y MS-3**. La identidad del usuario que dispara REST (si aplica) se valida contra **MS-1** (`ValidateToken`).

| Flujo de negocio (enunciado) | Responsable que dispara | MS-6 recibe vía |
|------------------------------|-------------------------|-----------------|
| Clave única al importar alumno | MS-3 (importación) | gRPC `SendBienvenida` o REST interno acordado |
| Baja de materia → correo al docente | MS-3 | gRPC `SendBajaNotif` |
| Cierre de materia → correo a alumnos | MS-4 (cierre) | gRPC `SendCierreMateria` |
| Recuperación de contraseña | MS-1 (forgot-password) | REST `reset-password` y/o gRPC `SendResetPassword` |

**Regla de arquitectura:** MS-6 **nunca** consulta la base de datos de otro microservicio.

---

## 2. Contrato gRPC oficial (`notificaciones.proto`)

Debe implementarse **paridad 1:1** entre servicer Python y el `.proto` versionado en `/proto`.

| RPC | Request | Response | Uso |
|-----|---------|----------|-----|
| `SendBienvenida` | `alumno_id`, `materia_id`, `clave_acceso` | `SendResponse` | Post-importación alumno |
| `SendBajaNotif` | `alumno_id`, `docente_id` (usuario_id), `materia_id` | `SendResponse` | Post-baja |
| `SendCierreMateria` | `materia_id` | `SendResponse` | Post-cierre materia |
| `SendResetPassword` | `email`, `token`, `reset_url` | `SendResponse` | Post-forgot-password |

**`SendResponse`:** `success` debe ser `false` si SMTP falló o si faltan datos críticos; `message` con texto seguro (sin stack traces en producción).

---

## 3. Endpoints REST (alineación backlog + gateway)

Prefijo detrás de Nginx: `/notificaciones/*` → puerto 8006.

| Método | Ruta lógica | Body esperado (JSON) | ISSUE |
|--------|-------------|----------------------|-------|
| POST | `/notificaciones/bienvenida` | `alumno_id`, `materia_id` (clave puede ir en body si MS-3 no usa solo gRPC — **acordar** con MS-3; el proto gRPC sí lleva `clave_acceso`) | 802 |
| POST | `/notificaciones/baja` | `alumno_id`, `docente_id`, `materia_id` (backlog lista 802/803; MS6 doc añade `materia_id` — necesario para asunto) | 803 |
| POST | `/notificaciones/cierre-materia` | `materia_id` | 804 |
| POST | `/notificaciones/reset-password` | `email`, `token`, `reset_url` | 805 |

**Formato de respuesta JSON** (obligatorio en el proyecto): `{ "success": true, "data": {...}, "message": "" }` salvo que el equipo unifique también errores SMTP en ese envoltorio.

---

## 4. Modelo de datos local

### `HistorialCorreo` (ISSUE-801)

| Campo | Tipo sugerido | Notas |
|-------|---------------|--------|
| `tipo` | CharField con choices | `bienvenida`, `baja`, `cierre_materia`, `reset_password` |
| `destinatario_email` | EmailField | Quién recibió el mensaje |
| `asunto` | CharField(255) | |
| `cuerpo` | TextField | HTML permitido; **escapar** datos dinámicos del usuario |
| `enviado_en` | DateTimeField auto | |
| `exitoso` | BooleanField | |
| `error_msg` | TextField nullable | Mensaje de error SMTP o gRPC upstream |

**Auditoría:** cada intento de envío (éxito o fallo) deja rastro para demo y manual técnico.

---

## 5. Clientes gRPC salientes (MS-6 → otros)

| Destino | Métodos | Para qué |
|---------|---------|----------|
| MS-3 | `GetAlumnoById`, `GetAlumnosByMateria`, y si aplica `GetDocenteByUsuarioId` | Emails, nombres, matrículas |
| MS-2 | `GetMateriaById` | Nombre NRC/sección/materia para plantillas |

**Configuración:** `MS_ALUMNOS_GRPC_HOST`, `MS_PERIODOS_GRPC_HOST`, puertos desde `.env.example`. Timeouts explícitos (p. ej. 5–10 s) y reintentos **solo** donde sea idempotente (mismo correo no duplicado si el caller reintenta — acordar idempotency key si hace falta).

---

## 6. Variables de entorno (mínimo)

```env
# Base
SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=...
DB_HOST=db-notificaciones
DB_NAME=agm_notificaciones_db
DB_USER=...
DB_PASSWORD=...
DB_CHARSET=utf8mb4
REST_PORT=8006
GRPC_PORT=50056

# gRPC clients
MS_AUTH_GRPC_HOST=ms-auth
MS_AUTH_GRPC_PORT=50051
MS_ALUMNOS_GRPC_HOST=ms-alumnos
MS_ALUMNOS_GRPC_PORT=50053
MS_PERIODOS_GRPC_HOST=ms-periodos
MS_PERIODOS_GRPC_PORT=50052

# SMTP (ejemplo Gmail; en prod usar credencial de aplicación o proveedor transaccional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=...
```

**Nunca** commitear valores reales.

---

## 7. Plan por issue (granular)

### ISSUE-801 — Configuración base Django (MS-6)

| # | Tarea | Criterio |
|---|--------|----------|
| 801.1 | `django-admin startproject` en `/ms-notificaciones/` | `manage.py check` sin errores |
| 801.2 | Motor MySQL 8, charset `utf8mb4` | Conexión desde contenedor |
| 801.3 | Instalar `djangorestframework`, `mysqlclient`, `grpcio`, `grpcio-tools`, `django-cors-headers`, `python-decouple` (o equivalente) | `requirements.txt` con versiones fijadas |
| 801.4 | App `notificaciones` (o nombre acordado) con modelo `HistorialCorreo` | Migraciones aplicadas |
| 801.5 | Backend email: `EMAIL_*` desde env; prueba `send_mail` en management command | Correo de prueba recibido |
| 801.6 | Dockerfile + entrypoint alineados al monorepo | Build OK |

**Fallos típicos:** MySQL no listo al arrancar (usar `depends_on` + healthcheck en Compose).

---

### ISSUE-802 — Correo de bienvenida al alumno

| # | Tarea | Criterio |
|---|--------|----------|
| 802.1 | Vista `POST .../bienvenida` | Valida payload; 400 si faltan campos |
| 802.2 | gRPC `GetAlumnoById(alumno_id)` | Obtener email y nombre; 404 si no existe |
| 802.3 | gRPC `GetMateriaById(materia_id)` | Nombre materia para plantilla |
| 802.4 | **Clave de acceso:** si REST no la recibe, el diseño correcto es que **solo** el caller que creó el usuario en MS-1 la envíe (gRPC `SendBienvenida` ya incluye `clave_acceso`) | Correo contiene clave o enlace de primer acceso según acuerdo de equipo |
| 802.5 | Plantilla HTML legible (BUAP, AGM) | Sin XSS: escapar nombre/materia |
| 802.6 | Insertar `HistorialCorreo` post-intento | `exitoso` / `error_msg` correctos |

**Prueba E2E:** MS-3 importa un alumno de prueba → se invoca MS-6 → bandeja recibe correo.

---

### ISSUE-803 — Notificación de baja al docente

| # | Tarea | Criterio |
|---|--------|----------|
| 803.1 | Payload: `alumno_id`, `docente_id`, `materia_id` | Alineado a `SendBajaRequest` en proto |
| 803.2 | Resolver email del docente vía MS-3 (`GetDocenteByUsuarioId` o flujo acordado) | No hardcodear correos |
| 803.3 | Cuerpo: nombre y matrícula del alumno + nombre de materia | Legible y profesional |
| 803.4 | Historial | Un registro por envío |

**Seguridad:** endpoint solo invocable por **servicio interno** (API key entre MS) o por usuario con rol permitido tras `ValidateToken`; el enunciado implica que la baja la hace el alumno vía MS-3, que a su vez llama a MS-6.

---

### ISSUE-804 — Cierre de materia (N destinatarios)

| # | Tarea | Criterio |
|---|--------|----------|
| 804.1 | `GetAlumnosByMateria(materia_id)` | Solo inscritos activos (MS-3 respeta bajas) |
| 804.2 | Bucle de envío: **threading** o `concurrent.futures` con límite de workers, o Celery si ya existe infra | La petición HTTP **no** debe bloquear más de timeout del gateway (ideal: responder 200 rápido con resumen “encolado N” si usan cola; backlog permite threading) |
| 804.3 | Registrar **cada** intento en `HistorialCorreo` | Trazabilidad por alumno |
| 804.4 | Manejo de fallo parcial | Respuesta indica cuántos OK / fallidos; no mentir con `success: true` global si hubo fallos masivos |

**Estrés:** probar con lista de ≥20 alumnos en local antes de prod.

---

### ISSUE-805 — Reset de contraseña

| # | Tarea | Criterio |
|---|--------|----------|
| 805.1 | Recibir `email`, `token`, `reset_url` | Compatible con MS-1 |
| 805.2 | Enlace HTTPS en plantilla | Variable `FRONTEND_RESET_PASSWORD_BASE_URL` en env si aplica |
| 805.3 | No incluir la contraseña nueva en el correo | Solo el enlace con token |
| 805.4 | Historial | Tipo `reset_password` |

---

### ISSUE-806 — Servidor gRPC (puerto 50056)

| # | Tarea | Criterio |
|---|--------|----------|
| 806.1 | Generar stubs desde `/proto/notificaciones.proto` | Mismo script que otros MS |
| 806.2 | Implementar `NotificacionesServicer` con los **4** RPC | Paridad con proto |
| 806.3 | Reutilizar la misma lógica que REST (servicio interno Django) | DRY: una capa `EmailService` |
| 806.4 | Servidor gRPC en hilo o proceso junto a Gunicorn | Puerto 50056 exclusivo |
| 806.5 | Pruebas con `grpcurl` o script Python | Evidencia en manual técnico |

**Errores gRPC:** usar `grpc.StatusCode.INVALID_ARGUMENT`, `NOT_FOUND`, `INTERNAL` según corresponda; no filtrar detalles internos al cliente.

---

## 8. Seguridad y cumplimiento

| Tema | Acción |
|------|--------|
| JWT | Endpoints REST públicos solo si el diseño lo exige; en general validar `Authorization: Bearer` vía MS-1 |
| Llamadas MS→MS | Considerar header/API key de servicio para `POST /notificaciones/*` si no van siempre con JWT de usuario |
| HTML | Usar templates Django con autoescape |
| Logs | No loguear `clave_acceso` ni tokens completos |
| Rate limiting | Opcional en MVP; documentar riesgo de abuso en `reset-password` |

---

## 9. Matriz de pruebas (obligatoria antes de “done”)

| ID | Caso | Entrada | Resultado esperado |
|----|------|---------|---------------------|
| P1 | Bienvenida | IDs válidos + clave | 200/201, correo recibido, historial `exitoso` |
| P2 | Bienvenida | `alumno_id` inexistente | 404 o gRPC NOT_FOUND mapeado a HTTP |
| P3 | Baja | IDs válidos | Docente recibe correo |
| P4 | Cierre | `materia_id` con 0 alumnos | 200 con mensaje claro; 0 envíos o aviso |
| P5 | Cierre | 50 alumnos | Sin timeout de gateway; todos en historial |
| P6 | Reset | Email válido | Enlace funciona en frontend cuando MS-1 valide token |
| P7 | SMTP caído | Cualquier envío | `exitoso=false`, `error_msg` útil, RPC `success=false` |

---

## 10. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Gmail bloquea “less secure apps” | App password o SendGrid/SES |
| Desfase proto/código | CI: `protoc` sobre `/proto` en PR |
| Timeout en cierre masivo | Thread pool acotado + respuesta con resumen; evolución a cola |
| Datos inconsistentes entre MS | Validar IDs antes de enviar; manejar `NOT_FOUND` de MS-2/3 |

---

## 11. Checklist de salida Epic 8

- [ ] ISSUE-801 … 806 completados en código y backlog marcado.  
- [ ] `proto/notificaciones.proto` implementado al 100 %.  
- [ ] Postman: carpeta MS-6 con 4 flujos mínimos.  
- [ ] Video / demo: **un correo real** visible (criterio enunciado §6.3).  
- [ ] README: URL 8006, variables SMTP, puerto gRPC 50056.  

---

## 12. Referencias

- `docs/backlog_AGM_completo.md` — Epic 8  
- `docs/Proyecto_Final_SW_AGM.md` — Módulo 7 Notificaciones  
- `docs/CONTEXTO_GLOBAL_PROYECTO.md` — §5 mapa gRPC  
- `proto/notificaciones.proto`  
