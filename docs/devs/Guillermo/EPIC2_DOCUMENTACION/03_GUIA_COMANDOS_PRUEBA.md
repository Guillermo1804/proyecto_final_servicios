# 03 — Guía de Comandos de Prueba

**Copy-paste ready comandos para validar gRPC localmente.**

---

## Prerequisitos

```bash
# Tener Docker Desktop corriendo
# Tener docker-compose instalado (viene con Docker Desktop)
cd /path/to/proyecto_final_servicios
```

---

## 1. Generar Stubs (si cambiaste .proto)

```bash
bash scripts/generate_all_protos.sh
```

**Esperado:** Sin errores, todos los `.proto` compilan.

---

## 2. Levantar Servicios Necesarios

### Opción A: Solo los 4 críticos (rápido)
```bash
docker compose up --build -d ms-alumnos ms-auth ms-calificaciones ms-asistencias
```

### Opción B: Todos los servicios
```bash
docker compose up --build -d
```

**Verificar estado:**
```bash
docker compose ps
# Debe mostrar todos los servicios en "Running"

# Ver logs (opcional, para debugging)
docker compose logs --tail=50 ms-alumnos
```

---

## 3. Smoke Tests — Validación Rápida

### Ejecutar script automático
```bash
bash scripts/grpc_smoke_tests.sh
```

**Esperado:** Levanta servicios, corre tests, imprime `Smoke tests completed successfully`.

### Manual — Test en ms-asistencias
```bash
docker compose exec ms-asistencias sh -lc "cd /app && PYTHONPATH=/app python tests/test_grpc_utils.py"
```

**Esperado:**
```
..
----------------------------------------------------------------------
Ran 2 tests in 0.000s

OK
```

### Manual — Test en ms-calificaciones
```bash
docker compose exec ms-calificaciones sh -lc "cd /app && PYTHONPATH=/app python tests/test_grpc_utils.py"
```

**Esperado:** Ídem (2 tests OK).

---

## 4. Pruebas Manuales con grpcurl

### Instalar grpcurl

**macOS:**
```bash
brew install grpcurl
```

**Linux:**
```bash
go get github.com/fullstorydev/grpcurl/cmd/grpcurl
```

**Windows:**
- Descargar desde https://github.com/fullstorydev/grpcurl/releases
- Guardar en `C:\Program Files\grpcurl\` o añadir a PATH

### Prueba 1: GetAlumnoById (ms-alumnos)

**Llamada gRPC:**
```bash
grpcurl -plaintext -d '{"alumno_id": 1}' \
  ms-alumnos:50053 \
  proto.AlumnosService/GetAlumnoById
```

**Esperado:** JSON response con datos del alumno (si existe en BD) o error `NOT_FOUND`.

**Nota:** Desde dentro del contenedor de Docker:
```bash
docker compose exec ms-alumnos sh -lc "grpcurl -plaintext -d '{\"alumno_id\": 1}' localhost:50053 proto.AlumnosService/GetAlumnoById"
```

### Prueba 2: ValidateToken (ms-auth)

```bash
# Token dummy (no será válido sin JWT válido, pero verifica conectividad)
grpcurl -plaintext -d '{"token": "dummy"}' \
  ms-auth:50051 \
  proto.AuthService/ValidateToken
```

**Esperado:** Error `UNAUTHENTICATED` o `INVALID_ARGUMENT` (token inválido es esperado).

### Prueba 3: Desde Cliente (ms-calificaciones → ms-alumnos)

Ejecutar script de prueba del cliente:
```bash
docker compose exec ms-calificaciones sh -lc "cd /app && python scripts/test_calificaciones_client.py"
```

**Esperado:** Output mostrando resultado de `GetAlumnoById` e intentos de `ValidateToken`.

---

## 5. Verificar Logs

### Logs de un servicio específico
```bash
docker compose logs --tail=100 -f ms-calificaciones
# -f = follow (stream en vivo); Ctrl+C para salir
```

### Buscar errores gRPC
```bash
docker compose logs ms-calificaciones | grep -i "grpc\|error\|exception"
```

---

## 6. Testing de Integración — Timeout

### Apagar un proveedor y verificar timeout

```bash
# 1. Servicio running normalmente
docker compose exec ms-calificaciones sh -lc "cd /app && python tests/test_grpc_utils.py"
# → OK

# 2. Apagar ms-alumnos
docker compose stop ms-alumnos

# 3. Intentar nuevamente — debe fallar con DEADLINE_EXCEEDED (timeout)
docker compose exec ms-calificaciones sh -lc "cd /app && python tests/test_grpc_utils.py"
# → Error: DEADLINE_EXCEEDED (5s timeout)

# 4. Reactivar
docker compose start ms-alumnos

# 5. Verificar que se recupera
sleep 2
docker compose exec ms-calificaciones sh -lc "cd /app && python tests/test_grpc_utils.py"
# → OK nuevamente
```

**Objetivo:** confirmar que los clientes responden rápidamente ante fallos en lugar de bloquear infinitamente.

---

## 7. Limpiar

### Parar servicios (mantener DB)
```bash
docker compose stop
```

### Parar y eliminar contenedores
```bash
docker compose down
```

### Parar, eliminar contenedores Y borrar volúmenes (reset total)
```bash
docker compose down -v
```

---

## 8. Troubleshooting

### Error: "service 'ms-alumnos' is not running"
**Solución:**
```bash
docker compose up -d ms-alumnos
docker compose logs ms-alumnos  # ver por qué falló
```

### Error: "Connection refused" en grpcurl
**Solución:**
- Verificar que el servicio está up: `docker compose ps`
- Esperar 5+ segundos tras `up` (healthcheck)
- Usar `localhost` si ejecutas desde host; usar nombre del servicio desde dentro de red Docker

### Error: "No module named 'grpc'"
**Solución:**
- Forzar rebuild: `docker compose build --no-cache ms-calificaciones`
- Verificar `requirements.txt` contiene `grpcio>=1.60`

### Error: "Test failed — import error"
**Solución:**
```bash
# Verificar que el archivo está dentro del contenedor
docker compose exec ms-calificaciones ls -la /app/tests/test_grpc_utils.py

# Si no existe, reconstruir
docker compose build --no-cache ms-calificaciones
docker compose up -d ms-calificaciones
```

---

## 9. Referencia Rápida — Comandos Más Usados

```bash
# Build + up
docker compose up --build -d ms-alumnos ms-auth ms-calificaciones ms-asistencias

# Tests
bash scripts/grpc_smoke_tests.sh
docker compose exec ms-asistencias sh -lc "cd /app && python tests/test_grpc_utils.py"

# Logs
docker compose logs --tail=50 -f ms-calificaciones

# Clean
docker compose down
```

---

## 10. CI/CD — GitHub Actions

Los smoke tests se ejecutan automáticamente en:
- **Trigger:** Push a `main` o Pull Request
- **Archivo:** `.github/workflows/grpc_smoke_tests.yml`
- **Acción:** Build + up servicios + run tests + down

Ver resultados en: https://github.com/[owner]/[repo]/actions
