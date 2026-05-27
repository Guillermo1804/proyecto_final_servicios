# 06 - Referencia de codigo

## Mapa de archivos clave

### Modelos
- `ms-asistencias/apps/core/models.py`
  - `SesionAsistencia`: sesiones de 10 min
  - `RegistroAsistencia`: asistencia por alumno (unique_together)

### Servicios de negocio
- `ms-asistencias/apps/core/services.py`
  - `SesionAsistenciaService.crear_sesion()`
  - `SesionAsistenciaService.cerrar_sesion()`
  - `SesionAsistenciaService.confirmar_sesion()`
  - `SesionAsistenciaService.solicitar_nueva_lista()`
  - `SesionAsistenciaService.obtener_sesion_activa()`

- `ms-asistencias/apps/core/qr_service.py`
  - `QRTokenService.generar_token_qr()`: payload + HMAC
  - `QRTokenService.validar_token_qr()`: check firma y timestamp

- `ms-asistencias/apps/core/attendance_service.py`
  - `AsistenciaRegistroService.registrar_asistencia()`: decodifica, valida, registra

- `ms-asistencias/apps/core/estadisticas_service.py`
  - `EstadisticasService.obtener_stats_sesion()`
  - `EstadisticasService.obtener_stats_alumno_materia()`
  - `EstadisticasService.obtener_stats_materia_resumen()`

### Utilidades
- `ms-asistencias/apps/core/utils.py`
  - `store_sesion_in_redis()`: guarda sesion con TTL 600
  - `get_sesion_from_redis()`: recupera sesion
  - `mark_qr_as_used()`: anti-replay (SET NX)
  - `qr_payload_hash()`: SHA256 del payload
  - `sign_qr_payload()`: HMAC SHA256
  - `verify_qr_payload()`: valida HMAC
  - `update_stats()`: incrementa contadores

### Vistas REST
- `ms-asistencias/apps/core/views.py`
  - `SesionAsistenciaViewSet`
    - `iniciar`: POST /sesiones/iniciar/
    - `cerrar`: DELETE /sesiones/{id}/cerrar/
    - `confirmar`: POST /sesiones/{id}/confirmar/
    - `solicitar_nueva`: POST /sesiones/{id}/solicitar-nueva/
    - `activa`: GET /sesiones/activa/
    - `stats`: GET /sesiones/{id}/stats/
    - `stats_materia`: GET /sesiones/stats_materia/
  
  - `RegistroAsistenciaViewSet`
    - `por_materia_hoy`: GET /registros/por_materia_hoy/
    - `historial`: GET /registros/historial/
    - `alumno_materia`: GET /registros/alumno_materia/
    - `stats_alumno_materia`: GET /registros/stats_alumno_materia/
  
  - `qr_generate`: GET /qr/generate/
  - `asistencia_registrar`: POST /asistencias/registrar/

### Rutas
- `ms-asistencias/apps/core/urls.py`
  - DefaultRouter para viewsets
  - Rutas custom para QR y registro

### Serializers
- `ms-asistencias/apps/core/serializers.py`
  - `SesionAsistenciaSerializer`
  - `IniciarSesionSerializer`
  - `RegistroAsistenciaSerializer`
  - `RegistroAsistenciaListSerializer`
  - `GenerarQRSerializer`
  - `QRTokenResponseSerializer`
  - `RegistrarAsistenciaSerializer`
  - `RegistroAsistenciaResponseSerializer`

### gRPC
- `ms-asistencias/grpc_server/servicer.py`
  - `AsistenciasServicer.GetAsistenciaAlumno()`
  - `AsistenciasServicer.GetEstadisticasAsistencia()`

- `ms-asistencias/apps/core/management/commands/grpc_server.py`
  - Management command para levantar servidor gRPC en 50055

- `ms-asistencias/proto_generated/asistencias_pb2.py`
- `ms-asistencias/proto_generated/asistencias_pb2_grpc.py`
  - Stubs generados desde `/proto/asistencias.proto`

### Clientes gRPC salientes
- `ms-asistencias/grpc_clients.py`
  - `validate_token()`: MS-1 auth
  - `get_alumno_by_id()`: MS-3
  - `is_alumno_en_materia()`: MS-3

### Configuracion
- `ms-asistencias/config/settings.py`: Django + Redis
- `ms-asistencias/config/urls.py`: URL dispatcher
- `ms-asistencias/.env.example`: variables de entorno
- `ms-asistencias/entrypoint.sh`: bootstrap script

---

## Flujo end-to-end de solicitud

### Scenario: Alumno registra asistencia

1. **Docente inicia pase**
   - REST: `POST /api/sesiones/iniciar/`
   - Vista: `SesionAsistenciaViewSet.iniciar()`
   - Servicio: `SesionAsistenciaService.crear_sesion()`
   - Accion: Crea `SesionAsistencia` (MySQL) y `store_sesion_in_redis()`

2. **Alumno genera QR**
   - REST: `GET /api/qr/generate/?materia_id=1&alumno_id=10`
   - Vista: `qr_generate()`
   - Servicio: `QRTokenService.generar_token_qr()`
   - Accion:
     - Valida sesion activa via MySQL
     - Valida alumno inscrito via gRPC MS-3
     - Crea payload JSON
     - Firma con `sign_qr_payload()` (HMAC SHA256)
     - Codifica base64
     - Calcula `qr_payload_hash()`
   - Response: `encoded_payload`, `expires_in`, `qr_hash`

3. **Alumno escanea y registra**
   - REST: `POST /api/asistencias/registrar/`
   - Body: `{"encoded_payload": "...base64..."}`
   - Vista: `asistencia_registrar()`
   - Servicio: `AsistenciaRegistroService.registrar_asistencia()`
   - Accion:
     - Decodifica base64 -> payload JSON
     - Verifica HMAC con `verify_qr_payload()`
     - Valida timestamp (ventana 30s) via `QRTokenService.validar_token_qr()`
     - Anti-replay: `mark_qr_as_used()` (SET qr_used:{hash} NX EX 120)
     - Obtiene sesion de MySQL
     - Calcula minutos transcurridos
     - Clasifica: presente (<=5) o retardo (>5)
     - `get_or_create()` en RegistroAsistencia (idempotencia)
     - `update_stats()` en Redis
   - Response: 201 con `exitoso=true`, `estado`, `minuto_registro`

4. **Docente consulta stats en vivo**
   - REST: `GET /api/sesiones/{id}/stats/`
   - Vista: `SesionAsistenciaViewSet.stats()`
   - Servicio: `EstadisticasService.obtener_stats_sesion()`
   - Accion: Query de RegistroAsistencia por estado, calcula porcentajes
   - Response: presentes, retardos, ausentes, total_registrados

5. **Docente cierra sesion**
   - REST: `DELETE /api/sesiones/{id}/cerrar/` o `POST /{id}/confirmar/`
   - Vista: `SesionAsistenciaViewSet.cerrar()` / `confirmar()`
   - Servicio: `SesionAsistenciaService.cerrar_sesion()` / `confirmar_sesion()`
   - Accion:
     - Marca `activa=False`, `estado='cerrada'` o `'confirmada'`
     - `delete_sesion_from_redis()` para limpiar cache
   - Response: sesion con estado actualizado

---

## Dependencias entre componentes

```
[Cliente REST]
    |
    v
[DRF ViewSet / Function View]
    |
    +-> [Service Layer] (logica de negocio)
    |   |
    |   +-> [Modelos Django]
    |   |
    |   +-> [Redis]
    |   |
    |   +-> [gRPC clients salientes]
    |
    +-> [Serializers]
    |
    v
[Respuesta JSON]

[gRPC Servicer]
    |
    +-> [Modelos Django]
    |
    +-> [gRPC clients salientes]
    |
    v
[Respuesta protobuf]
```

---

## Puntos criticos para mantenimiento

1. **HMAC signing**: Cambios a `sign_qr_payload()` o `QR_HMAC_SECRET` invalidan tokens en vuelo.
2. **Anti-replay Redis**: Si se limpian claves sin control, puede permitir duplicados.
3. **Sesion TTL**: Reducir TTL de 600s rompe ventana de 10 minutos.
4. **Unique together**: No remover la restriccion `(sesion, alumno_id)`.
5. **gRPC stubs**: Si se cambia proto, regenerar stubs en `proto_generated/`.

---

## Extension futura

Para agregar nuevos endpoints o servicios:

1. Crear metodo en servicio correspondiente
2. Crear o extender serializer
3. Agregar view/action con decorador @action
4. Router maneja rutas automaticamente
5. Seguir patron existente de manejo de errores (ValidationError -> 400)
