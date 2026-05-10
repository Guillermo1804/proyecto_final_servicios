# 📱 MS-5: Asistencias QR — Especificación para IA

> **Lee primero**: `docs/CONTEXTO_GLOBAL_PROYECTO.md`

---

## Identidad

| Campo | Valor |
|-------|-------|
| **Carpeta** | `/ms-asistencias/` |
| **Puerto REST** | 8005 |
| **Puerto gRPC** | 50055 |
| **BD** | MySQL – `agm_asistencias_db` + **Redis** (sesiones en vivo) |
| **Responsabilidad** | Sesiones de asistencia 10 min, tokens QR dinámicos con HMAC, anti-replay, clasificación Presente/Retardo |

## Dependencias extras
```
redis>=5.0
django-redis>=5.4
cryptography>=42.0
```

## Modelos

### `SesionAsistencia`
- `materia_id` (IntegerField)
- `docente_id` (IntegerField)
- `inicio` (DateTimeField auto_now_add)
- `fin` (DateTimeField) — inicio + 10 min
- `activa` (BooleanField default=True)
- **Constraint**: solo 1 sesión activa por materia_id

### `RegistroAsistencia`
- `sesion` (FK → SesionAsistencia)
- `alumno_id` (IntegerField)
- `timestamp_registro` (DateTimeField)
- `estado` (CharField choices: 'presente', 'retardo')
- **unique_together**: `['sesion', 'alumno_id']` — un alumno solo registra 1 vez por sesión

## Endpoints REST

### Sesiones
- `POST /sesiones/iniciar` — body: `{materia_id}`. Auth: docente de la materia.
  - Crear sesión en MySQL con `fin = ahora + 10 min`
  - Guardar en Redis: `sesion:{id}` con TTL=600s
  - Validar: no existe otra sesión activa para esa materia
  - Response: `{sesion_id, inicio, fin}`

- `DELETE /sesiones/:id/cerrar` — docente cierra manualmente. Marca `activa=False`

- `GET /sesiones/:materiaId/activa` — ¿hay sesión activa? Response: datos de la sesión o 404

### QR del Alumno
- `GET /qr/generate?materia_id=:id` — Auth: alumno inscrito en la materia
  - Genera payload: `alumno_id|sesion_id|timestamp|hmac_signature`
  - HMAC con clave secreta del servidor
  - Validez: 30 segundos
  - El frontend convierte este string en QR visual
  - Response: `{ "qr_payload": "...", "expires_in": 30 }`

### Registro de Asistencia
- `POST /asistencias/registrar` — Auth: docente. Body: `{qr_payload}`
  - Verificar firma HMAC
  - Verificar timestamp (no expirado, <30s)
  - Verificar en Redis que NO fue usado: `GET qr_used:{hash}` → si existe, rechazar
  - Verificar sesión activa en Redis
  - Calcular estado:
    - **Presente**: ≤5 min desde inicio de sesión
    - **Retardo**: >5 min y ≤10 min
  - Guardar en MySQL
  - Marcar como usado en Redis: `SET qr_used:{hash} 1 EX 600`
  - Response 400 si: QR inválido, expirado, ya usado, sesión cerrada

### Consultas
- `GET /asistencias/:materiaId/hoy` — asistencias de hoy
- `GET /asistencias/:materiaId/historial?page=1&limit=10&fecha=2026-05-10` — historial paginado
- `GET /asistencias/alumno/:alumnoId/materia/:materiaId` — historial de un alumno
- `GET /sesiones/:id/stats` — stats en tiempo real durante sesión: total, presentes, retardos, ausentes

## Servidor gRPC (Puerto 50055)
```protobuf
syntax = "proto3";
package asistencias;
service AsistenciasService {
  rpc GetAsistenciaAlumno(GetAsistenciaAlumnoRequest) returns (AsistenciaListResponse);
  rpc GetEstadisticasAsistencia(GetEstadisticasRequest) returns (EstadisticasResponse);
}
// GetAsistenciaAlumno: alumno_id + materia_id → lista de {fecha, estado}
// GetEstadisticasAsistencia: materia_id → {total_sesiones, presentes, retardos, ausentes, porcentaje}
```

## Clientes gRPC
| Destino | Método | Cuándo |
|---------|--------|--------|
| MS-1 | ValidateToken | Cada request |
| MS-3 | GetAlumnoById, IsAlumnoEnMateria | Validar QR, obtener datos alumno |

## Reglas Críticas
1. Sesiones duran EXACTAMENTE 10 minutos (TTL Redis 600s)
2. Presente: ≤5 min. Retardo: >5 min y ≤10 min
3. Anti-replay: el mismo QR NO puede registrarse 2 veces (Redis marker)
4. QR payload cambia cada 30 segundos
5. Solo 1 sesión activa por materia a la vez
6. Cierre automático por TTL de Redis (+ cron/celery para marcar en MySQL)

## Variables de Entorno extras
```env
REDIS_HOST=redis
REDIS_PORT=6379
QR_HMAC_SECRET=clave-secreta-para-firmar-qr
```
