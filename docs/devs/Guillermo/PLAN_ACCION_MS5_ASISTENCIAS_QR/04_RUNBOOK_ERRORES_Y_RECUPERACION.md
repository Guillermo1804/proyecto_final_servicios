# 04 - Runbook de errores y recuperacion

## Uso de este runbook

Para cada error se documenta:
- Sintoma
- Causa probable
- Diagnostico rapido
- Solucion
- Verificacion de cierre

---

## E1) "No se puede decodificar el payload QR"

### Sintoma
Endpoint `POST /api/asistencias/registrar/` retorna 400 con error de decode.

### Causa probable
- `encoded_payload` no esta en base64 valido.
- Payload truncado por cliente.

### Diagnostico rapido
- Validar que el cliente envia exactamente el `encoded_payload` retornado por `/api/qr/generate/`.
- Revisar logs del backend para excepcion de decode/json.

### Solucion
- Regenerar QR y reintentar dentro de ventana de 30s.
- Corregir serializacion del cliente (no alterar caracteres `+`, `/`, `=`).

### Verificacion
- El registro retorna 201 y mensaje de asistencia registrada.

---

## E2) "Firma de QR invalida"

### Sintoma
`POST /api/asistencias/registrar/` retorna 400 por HMAC.

### Causa probable
- Payload alterado en cliente.
- `QR_HMAC_SECRET` inconsistente entre entornos.

### Diagnostico rapido
- Comparar `QR_HMAC_SECRET` del contenedor que genera y del que valida.
- Revisar si existe manipulación del payload en frontend.

### Solucion
- Unificar variable `QR_HMAC_SECRET`.
- Regenerar token QR.

### Verificacion
- `GET /api/qr/generate/` + `POST /api/asistencias/registrar/` exitosos.

---

## E3) "Token expirado" o "timestamp en el futuro"

### Sintoma
Rechazo por ventana temporal.

### Causa probable
- QR usado despues de 30 segundos.
- Desfase horario de contenedor/host.

### Diagnostico rapido
- Medir delta entre generacion y consumo.
- Revisar hora de contenedores.

### Solucion
- Reintentar con QR recien generado.
- Sincronizar reloj/NTP del host y contenedores.

### Verificacion
- Token nuevo registrado dentro de 30s.

---

## E4) "Este QR ya fue registrado" (anti-replay)

### Sintoma
Segundo intento del mismo payload falla.

### Causa probable
- Reuso de payload ya registrado.
- Reintentos automáticos del cliente con mismo body.

### Diagnostico rapido
- Revisar si se envia exactamente el mismo `encoded_payload`.
- Verificar duplicidad en logs del cliente.

### Solucion
- Generar nuevo QR.
- Corregir logica cliente para no reintentar con payload viejo.

### Verificacion
- Nuevo payload registra correctamente.

---

## E5) "No hay sesion activa" / "Sesion cerrada"

### Sintoma
No se puede generar o registrar asistencia.

### Causa probable
- Sesion no iniciada.
- Sesion expirada/cerrada/confirmada.
- Redis limpio sin sesion activa y sesion en DB ya inactiva.

### Diagnostico rapido
- Consultar `GET /api/sesiones/activa/?materia_id=...`.
- Revisar estado de sesion en DB (activa, estado).

### Solucion
- Docente inicia nueva sesion.
- Si corresponde, usar `solicitar-nueva` y luego `iniciar`.

### Verificacion
- Endpoint `activa` responde con sesion valida.

---

## E6) Error de conexion a Redis

### Sintoma
Fallas en anti-replay, stats en vivo o manejo de sesion cacheada.

### Causa probable
- Contenedor Redis caido o hostname incorrecto.
- `REDIS_HOST`/`REDIS_PORT` mal configurados.

### Diagnostico rapido
- Revisar `docker compose ps`.
- Probar conexion desde contenedor MS-5.

### Solucion
- Levantar Redis.
- Corregir variables de entorno.
- Reiniciar MS-5.

### Verificacion
- Flujo de sesion y registro funciona sin errores de cache.

---

## E7) gRPC server no levanta en 50055

### Sintoma
MS-7 no puede consumir RPCs de asistencias.

### Causa probable
- `grpc_server` command no ejecutado.
- Error al importar servicer.
- Puerto ocupado.

### Diagnostico rapido
- Revisar logs de `entrypoint.sh`.
- Confirmar presencia de mensaje "Servidor gRPC iniciado".

### Solucion
- Verificar `apps/core/management/commands/grpc_server.py`.
- Verificar `grpc_server/servicer.py`.
- Liberar o cambiar `GRPC_PORT`.

### Verificacion
- RPC responde sin UNIMPLEMENTED.

---

## E8) Error por version de grpcio/protobuf

### Sintoma
Excepcion de runtime en `*_pb2_grpc.py` por version incompatible.

### Causa probable
- `grpcio` menor a version usada al generar stubs.

### Diagnostico rapido
- Leer mensaje exacto de runtime en logs.

### Solucion
- Actualizar `grpcio` y `grpcio-tools` o regenerar stubs con version compatible.

### Verificacion
- Arranque limpio del servidor gRPC.

---

## E9) MySQL no disponible al iniciar contenedor

### Sintoma
MS-5 queda esperando DB o falla migracion.

### Causa probable
- Servicio DB no listo.
- Credenciales invalidas.

### Diagnostico rapido
- Revisar logs de entrypoint (bucle de espera).
- Verificar variables DB.

### Solucion
- Levantar DB antes de MS-5.
- Corregir credenciales/host/puerto.

### Verificacion
- Migraciones aplicadas y servicio arriba.

---

## E10) Inconsistencia con MS-3 (alumno no encontrado)

### Sintoma
QR no se genera o estadisticas gRPC sin matricula/nombre.

### Causa probable
- MS-3 caido o timeout.
- alumno_id no existe.

### Diagnostico rapido
- Revisar conectividad gRPC saliente a MS-3.
- Validar alumno en MS-3.

### Solucion
- Recuperar MS-3 o ajustar timeout.
- Corregir ids en pruebas.

### Verificacion
- `is_alumno_en_materia` retorna true para casos validos.

---

## Procedimiento de recuperacion rapida (incidente)

1. Confirmar estado de contenedores:
```bash
docker compose ps
```

2. Revisar logs MS-5:
```bash
docker compose logs -f ms-asistencias
```

3. Validar salud minima:
- REST responde.
- gRPC arranca en 50055.
- Redis y DB alcanzables.

4. Si el estado de sesion quedo corrupto:
- Cerrar/confirmar la sesion.
- Ejecutar `solicitar-nueva`.
- Iniciar una nueva sesion limpia.

5. Repetir prueba E2E basica:
- iniciar -> generate qr -> registrar -> stats.
