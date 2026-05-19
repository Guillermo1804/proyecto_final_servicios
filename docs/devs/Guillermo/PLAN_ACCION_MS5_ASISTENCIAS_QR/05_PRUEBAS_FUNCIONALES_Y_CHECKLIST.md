# 05 - Pruebas funcionales y checklist

## Matriz de pruebas obligatorias (del plan de acción)

| ID | Caso de Prueba | Precondicion | Pasos | Resultado Esperado | Estado |
|----|----------------|--------------|-------|-------------------|--------|
| A1 | Iniciar sesion | MS-5 levantado, token valido | POST /sesiones/iniciar con materia_id, docente_id | 201 con sesion activa=true en MySQL y en Redis con TTL 600 | ✅ |
| A2 | Iniciar duplicado | Sesion activa existe | POST /sesiones/iniciar misma materia_id | 400 con error de sesion duplicada | ✅ |
| A3 | QR valido minuto 3 | Sesion activa, alumno inscrito | GET /qr/generate en t=180s, POST /registrar en t<185s | 201 con estado="presente", minuto_registro=3 | ✅ |
| A4 | QR valido minuto 7 | Sesion activa, alumno inscrito | GET /qr/generate en t=420s, POST /registrar en t<425s | 201 con estado="retardo", minuto_registro=7 | ✅ |
| A5 | Mismo QR dos veces | QR valido registrado | POST /registrar con mismo encoded_payload | Primera: 201, Segunda: 400 anti-replay | ✅ |
| A6 | QR con firma incorrecta | Payload disponible | POST /registrar con payload alterado | 400 "Firma de QR invalida" | ✅ |
| A7 | Sesion expirada | Sesion existe, >10 min | POST /registrar tras sesion vencida | 400 "Sesion expiro" | ✅ |
| A8 | gRPC GetEstadisticasAsistencia | Registros en BD | RPC con materia_id | Response con lista de alumnos, presentes, retardos, ausentes, porcentajes | ✅ |

---

## Checklist de salida Epic 7

### Codigo y arquitectura
- [x] ISSUE-701 ... 708 completados
- [x] Modelos Django: `SesionAsistencia`, `RegistroAsistencia`
- [x] Servicios de negocio: sesion, QR, registro, estadisticas
- [x] Vistas REST con autenticacion
- [x] Servidor gRPC con implementacion real
- [x] Utilidades: Redis, HMAC, anti-replay

### Integracion
- [x] MySQL `agm_asistencias_db` con migraciones
- [x] Redis para cache y coordinacion
- [x] gRPC saliente a MS-1 (auth) y MS-3 (alumnos)
- [x] gRPC entrante desde MS-7 (reportes)

### Configuracion
- [x] `.env.example` con todas las variables
- [x] `settings.py` con Redis y HMAC
- [x] `entrypoint.sh` con auto-setup
- [x] `docker-compose` entry para MS-5

### Documentacion
- [x] README de plan
- [x] Resumen tecnico
- [x] Detalle por issue
- [x] Guia operativa Docker
- [x] Runbook de errores
- [x] Pruebas funcionales
- [x] Referencia de codigo

### Demo y validacion
- [x] Anti-replay demostrable (caso A5)
- [x] Clasificacion presente/retardo (casos A3, A4)
- [x] Cierre automatico por TTL (validable en Redis)
- [x] Flujo docente + alumno completo

---

## Pasos de validacion manual (smoke test)

### 1) Verificar salud basica

```bash
# Terminal 1: Ver logs
docker compose logs -f ms-asistencias

# Terminal 2: Verificar REST
curl -s http://localhost:8005/health/ | jq .

# Terminal 3: Verificar gRPC (requiere herramienta grpcurl)
grpcurl -plaintext localhost:50055 list
# Esperado: asistencias.AsistenciasService
```

### 2) Flujo E2E minimo

```bash
# 2a. Iniciar sesion
curl -X POST http://localhost:8005/api/sesiones/iniciar/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"materia_id": 1, "docente_id": 5}'

# Guardar sesion_id de la respuesta como $SESION_ID

# 2b. Generar QR
curl -s "http://localhost:8005/api/qr/generate/?materia_id=1&alumno_id=10" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Guardar encoded_payload como $QR_PAYLOAD

# 2c. Registrar asistencia
curl -X POST http://localhost:8005/api/asistencias/registrar/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"encoded_payload\": \"$QR_PAYLOAD\"}"

# Resultado esperado: 201 con exitoso=true, estado=presente

# 2d. Consultar stats
curl -s "http://localhost:8005/api/sesiones/$SESION_ID/stats/" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Esperado: presentes=1, retardos=0, ausentes=0

# 2e. Cerrar sesion
curl -X DELETE http://localhost:8005/api/sesiones/$SESION_ID/cerrar/ \
  -H "Authorization: Bearer $TOKEN"

# Esperado: 200 con sesion.activa=false
```

### 3) Validar anti-replay

```bash
# Con misma $QR_PAYLOAD, intentar registrar 2 veces
# Primera: 201 exitoso
# Segunda: 400 "Este QR ya fue registrado"
```

### 4) Validar gRPC

```bash
grpcurl -plaintext \
  -d '{"alumno_id": 10, "materia_id": 1}' \
  localhost:50055 asistencias.AsistenciasService/GetAsistenciaAlumno
  
# Esperado: respuesta con presentes, retardos, ausentes, registros
```

---

## Criterios de aceptacion para QA

- [ ] Todos los casos A1-A8 pasan.
- [ ] Logs limpios sin excepciones no controladas.
- [ ] gRPC responde con datos coherentes vs MySQL.
- [ ] Anti-replay funciona (duplicado rechazado).
- [ ] Cierre de sesion limpia Redis y marca inactiva en MySQL.
- [ ] Flujo docente (iniciar -> confirmar/cerrar) funciona.
- [ ] Flujo alumno (generar QR -> registrar) funciona.
- [ ] Estadisticas en vivo reflejan registros acumulados.

---

## Casos de regresion a validar

Cada cambio futuro debe validar:
- Sesion no se duplica por materia.
- QR con HMAC incorrecto rechazado.
- Anti-replay por hash funciona.
- Clasificacion presente/retardo por minuto correcta.
- gRPC no retorna UNIMPLEMENTED.
- Redis limpio al cerrar sesion.
