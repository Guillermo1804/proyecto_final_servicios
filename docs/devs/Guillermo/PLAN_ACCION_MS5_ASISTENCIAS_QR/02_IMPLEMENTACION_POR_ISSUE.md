# 02 - Implementacion por issue (Epic 7)

## ISSUE-701 - Configuracion base Django

### Implementado
- Configuracion Django + DRF.
- Integracion MySQL (`agm_asistencias_db`) y Redis.
- Registro de app `apps.core`.
- Modelos base y migracion inicial.
- Variables de entorno para puertos, DB, Redis y HMAC.

### Evidencia en codigo
- `ms-asistencias/config/settings.py`
- `ms-asistencias/apps/core/models.py`
- `ms-asistencias/apps/core/migrations/0001_initial.py`
- `ms-asistencias/.env.example`

### Criterios cubiertos
- Estructura base funcional.
- Soporte Redis habilitado.
- Modelado con restriccion anti-duplicado por sesion/alumno.

---

## ISSUE-702 - Gestion de sesiones

### Implementado
- Inicio de sesion con control de duplicados (Redis + MySQL).
- Cierre manual de sesion y limpieza de claves Redis.
- Consulta de sesion activa por materia.
- Inicializacion de contadores para stats.

### Evidencia en codigo
- `ms-asistencias/apps/core/services.py` (`crear_sesion`, `cerrar_sesion`, `obtener_sesion_activa`)
- `ms-asistencias/apps/core/views.py` (`iniciar`, `cerrar`, `activa`)

### Criterios cubiertos
- Unica sesion activa por materia.
- Persistencia en MySQL con estado de sesion.
- Redis TTL de 600 segundos.

---

## ISSUE-703 - Generacion de QR

### Implementado
- Endpoint para generar QR por alumno/materia.
- Firma HMAC SHA256 del payload.
- Ventana de validez de 30 segundos.
- Validacion de alumno inscrito via gRPC MS-3.

### Evidencia en codigo
- `ms-asistencias/apps/core/qr_service.py`
- `ms-asistencias/apps/core/views.py` (`qr_generate`)

### Criterios cubiertos
- Payload con alumno, sesion, materia y timestamp.
- Respuesta con `expires_in`, hash y payload codificado en base64.

---

## ISSUE-704 - Registro de asistencia

### Implementado
- Endpoint de registro por payload QR codificado.
- Decodificacion + validacion estructural.
- Verificacion HMAC + validez temporal.
- Anti-replay Redis por hash y TTL corto.
- Idempotencia con `get_or_create` y `unique_together`.

### Evidencia en codigo
- `ms-asistencias/apps/core/attendance_service.py`
- `ms-asistencias/apps/core/views.py` (`asistencia_registrar`)
- `ms-asistencias/apps/core/utils.py` (`mark_qr_as_used`, `verify_qr_payload`, `update_stats`)

### Criterios cubiertos
- Evita doble registro del mismo QR.
- Clasifica presente/retardo por minuto de sesion.
- Actualiza contadores en Redis para tiempo real.

---

## ISSUE-705 - Consultas

### Implementado
- Registros de hoy por materia.
- Historial por materia con paginacion y filtros de fecha.
- Consulta alumno-materia con resumen.

### Evidencia en codigo
- `ms-asistencias/apps/core/views.py` (`por_materia_hoy`, `historial`, `alumno_materia`)

### Criterios cubiertos
- Query de historico con `page`, `limit` y rango de fechas.
- Informacion lista para dashboards y seguimiento.

---

## ISSUE-706 - Estadisticas en tiempo real

### Implementado
- Stats por sesion en vivo.
- Stats agregadas por materia.
- Stats por alumno/materia.
- Servicio dedicado de estadisticas.

### Evidencia en codigo
- `ms-asistencias/apps/core/estadisticas_service.py`
- `ms-asistencias/apps/core/views.py` (`stats`, `stats_materia`, `stats_alumno_materia`)

### Criterios cubiertos
- Conteos de presentes, retardos, ausentes.
- Datos orientados a UI docente y consumo interno.

---

## ISSUE-707 - Servidor gRPC

### Implementado
- Servidor gRPC en puerto 50055.
- Implementacion real (no mock) de:
  - `GetAsistenciaAlumno`
  - `GetEstadisticasAsistencia`
- Enriquecimiento opcional de alumno con MS-3.

### Evidencia en codigo
- `ms-asistencias/grpc_server/servicer.py`
- `ms-asistencias/apps/core/management/commands/grpc_server.py`
- `ms-asistencias/entrypoint.sh`

### Criterios cubiertos
- Respuestas consistentes con `proto/asistencias.proto`.
- Datos calculados desde MySQL.

---

## ISSUE-708 - Confirmar / solicitar nueva lista

### Implementado
- `POST /sesiones/{id}/confirmar/`:
  - Marca sesion `confirmada`.
  - Desactiva sesion.
  - Limpia Redis.
- `POST /sesiones/{id}/solicitar-nueva/`:
  - Invalida sesion actual (`cerrada`).
  - Desactiva sesion.
  - Limpia Redis para habilitar nueva lista.

### Evidencia en codigo
- `ms-asistencias/apps/core/services.py` (`confirmar_sesion`, `solicitar_nueva_lista`)
- `ms-asistencias/apps/core/views.py` (`confirmar`, `solicitar_nueva`)

### Criterios cubiertos
- Cierre funcional del flujo de pase de lista.
- Reapertura controlada ante irregularidades.

---

## Resultado del plan

- Epic 7 completada: 8/8 issues.
- Integracion REST + Redis + MySQL + gRPC operativa.
- Base documental lista para transferencia a nuevo integrante.
