# 01 - Resumen tecnico

## 1) Contexto del MS-5

MS-5 implementa el pase de lista por QR dinamico con restricciones de tiempo y controles anti-fraude:
- Sesion por materia de 10 minutos.
- Token QR con validez de 30 segundos.
- Clasificacion automatica: presente (<=5 min), retardo (>5 y <=10 min).
- Anti-replay por hash del payload en Redis.
- Exposicion REST para front/back-office.
- Exposicion gRPC para consumo por MS-7.

## 2) Arquitectura aplicada

### Persistencia y consistencia

- Fuente de verdad: MySQL (`SesionAsistencia`, `RegistroAsistencia`).
- Cache y coordinacion temporal: Redis.
- Redis no reemplaza MySQL; acelera lookup de sesion y anti-replay.

### Comunicacion entre servicios

- MS-5 consume:
  - MS-1 (`ValidateToken`) para autenticacion/autorizacion.
  - MS-3 (`GetAlumnoById`, `IsAlumnoEnMateria`) para validacion de alumno.
- MS-5 expone:
  - REST para sesiones, QR, registros y estadisticas.
  - gRPC para consultas agregadas de asistencia.

## 3) Reglas de negocio implementadas

### Sesion de asistencia

- Solo una sesion activa por materia.
- Se crea en MySQL y se replica estado en Redis con TTL 600 segundos.
- Se puede cerrar, confirmar o invalidar para abrir nueva lista.

### QR dinamico

- Payload incluye `alumno_id`, `sesion_id`, `materia_id`, `timestamp`.
- Firma HMAC SHA256 con `QR_HMAC_SECRET`.
- Token invalido si:
  - Firma no coincide.
  - Timestamp supera ventana de 30 segundos.
  - Sesion no activa, no vigente o de materia distinta.

### Registro de asistencia

- Anti-replay: `qr_used:{hash}` con TTL corto (120s).
- Idempotencia por `unique_together (sesion, alumno_id)`.
- Estado calculado por minuto de sesion.
- Actualizacion de contadores en Redis para stats en vivo.

## 4) Endpoints y operaciones principales

### REST

- Sesiones:
  - `POST /api/sesiones/iniciar/`
  - `DELETE /api/sesiones/{id}/cerrar/`
  - `POST /api/sesiones/{id}/confirmar/`
  - `POST /api/sesiones/{id}/solicitar-nueva/`
  - `GET /api/sesiones/activa/?materia_id=...`
  - `GET /api/sesiones/{id}/stats/`
  - `GET /api/sesiones/stats_materia/?materia_id=...`
- QR y registro:
  - `GET /api/qr/generate/?materia_id=...&alumno_id=...`
  - `POST /api/asistencias/registrar/`
- Consultas de registros:
  - `GET /api/registros/por_materia_hoy/?materia_id=...`
  - `GET /api/registros/historial/?materia_id=...&page=...&limit=...`
  - `GET /api/registros/alumno_materia/?alumno_id=...&materia_id=...`
  - `GET /api/registros/stats_alumno_materia/?alumno_id=...&materia_id=...`

### gRPC (puerto 50055)

- `GetAsistenciaAlumno(alumno_id, materia_id)`
- `GetEstadisticasAsistencia(materia_id)`

## 5) Componentes clave

- Modelos: `apps/core/models.py`
- Servicios de sesion: `apps/core/services.py`
- Servicio QR: `apps/core/qr_service.py`
- Servicio registro: `apps/core/attendance_service.py`
- Servicio estadisticas: `apps/core/estadisticas_service.py`
- Vistas REST: `apps/core/views.py`
- Router REST: `apps/core/urls.py`
- gRPC servicer: `grpc_server/servicer.py`
- gRPC command: `apps/core/management/commands/grpc_server.py`
- Config Redis/HMAC: `config/settings.py`
- Entrypoint Docker: `entrypoint.sh`

## 6) Resultado final del plan

Se completo el plan por fases hasta ISSUE-708 y se dejaron mecanismos de operacion y recuperacion para que el modulo sea mantenible por terceros.
