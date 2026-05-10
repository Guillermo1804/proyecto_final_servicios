# 📧 MS-6: Notificaciones — Especificación para IA

> **Lee primero**: `docs/CONTEXTO_GLOBAL_PROYECTO.md`

---

## Identidad

| Campo | Valor |
|-------|-------|
| **Carpeta** | `/ms-notificaciones/` |
| **Puerto REST** | 8006 |
| **Puerto gRPC** | 50056 |
| **BD** | MySQL – `agm_notificaciones_db` |
| **Responsabilidad** | Envío de correos transaccionales vía SMTP: bienvenida, baja, cierre de materia, reset password |

## Dependencias extras
Ninguna extra — Django tiene `django.core.mail` integrado.

## Modelo

### `HistorialCorreo`
- `tipo` (CharField choices: 'bienvenida', 'baja', 'cierre_materia', 'reset_password')
- `destinatario_email` (EmailField)
- `asunto` (CharField 255)
- `cuerpo` (TextField) — contenido HTML del correo
- `enviado_en` (DateTimeField auto_now_add)
- `exitoso` (BooleanField)
- `error_msg` (TextField, blank, null)

## Endpoints REST

- `POST /notificaciones/bienvenida` — body: `{alumno_id, materia_id, clave_acceso}`
  - gRPC a MS-3: GetAlumnoById → nombre, email
  - gRPC a MS-2: GetMateriaById → nombre materia
  - Enviar correo con: nombre, materia, clave de acceso
  - Guardar en HistorialCorreo

- `POST /notificaciones/baja` — body: `{alumno_id, docente_id, materia_id}`
  - gRPC a MS-3: GetAlumnoById, GetDocenteByUsuarioId
  - Enviar correo AL DOCENTE notificando la baja del alumno

- `POST /notificaciones/cierre-materia` — body: `{materia_id}`
  - gRPC a MS-3: GetAlumnosByMateria → lista de alumnos
  - gRPC a MS-2: GetMateriaById → nombre materia
  - Enviar correo a CADA alumno (usar threading para no bloquear)

- `POST /notificaciones/reset-password` — body: `{email, token, reset_url}`
  - Enviar correo con enlace de restablecimiento

## Servidor gRPC (Puerto 50056)
```protobuf
syntax = "proto3";
package notificaciones;
service NotificacionesService {
  rpc SendBienvenida(SendBienvenidaRequest) returns (SendResponse);
  rpc SendBajaNotif(SendBajaRequest) returns (SendResponse);
  rpc SendCierreMateria(SendCierreMateriaRequest) returns (SendResponse);
  rpc SendResetPassword(SendResetPasswordRequest) returns (SendResponse);
}
// SendBienvenida: alumno_id, materia_id, clave_acceso → bool success
// SendBajaNotif: alumno_id, docente_id, materia_id → bool success
// SendCierreMateria: materia_id → bool success (envía a todos los alumnos)
// SendResetPassword: email, token, reset_url → bool success
message SendResponse { bool success = 1; string message = 2; }
```

## Clientes gRPC
| Destino | Método | Cuándo |
|---------|--------|--------|
| MS-1 | ValidateToken | Requests REST protegidos |
| MS-3 | GetAlumnoById, GetAlumnosByMateria, GetDocenteByUsuarioId | Obtener datos para correos |
| MS-2 | GetMateriaById | Obtener nombre de materia para correos |

## Variables de Entorno extras
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=agm.notificaciones@gmail.com
EMAIL_HOST_PASSWORD=app-password-de-google
DEFAULT_FROM_EMAIL=AGM Sistema <agm.notificaciones@gmail.com>
FRONTEND_URL=https://agm-frontend.vercel.app
```

## Reglas Críticas
1. TODOS los correos enviados se registran en HistorialCorreo (auditoría)
2. El envío masivo (cierre de materia) debe ser asíncrono (threading o similar)
3. Si un correo falla, registrar el error pero NO crashear el servicio
4. El enlace de reset password usa la variable `FRONTEND_URL`
