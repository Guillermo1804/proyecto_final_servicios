# 01 — Estado de Implementación por ISSUE

**Epic 2: Arquitectura y Comunicación gRPC**  
**Actualizado:** Mayo 18, 2026

---

## ISSUE-201 — Definición de Contratos `.proto`

| # | Tarea | Criterio | Estado |
|---|-------|----------|--------|
| 201.1 | Un `.proto` por servicio | Estructura alineada al backlog | ✅ OK |
| 201.2 | Mensajes `Request`/`Response` por RPC | Sin ambigüedad en campos | ✅ OK |
| 201.3 | Compilación global de 7 archivos | Desde raíz sin errores | ✅ OK |
| 201.4 | Control de versiones | Cambios breaking documentados | ✅ OK |
| 201.5 | Coherencia con contexto global § 5 | Flechas = métodos RPC | ✅ OK |

**Archivos entregados:**
- `proto/auth.proto` (ValidateToken, GetUserById, CheckRole)
- `proto/periodos.proto` (GetMateriaById, GetMateriasByDocente, GetPeriodoActivo)
- `proto/alumnos.proto` (GetAlumnosByMateria, GetAlumnoById, IsAlumnoEnMateria)
- `proto/calificaciones.proto` (existente, mejorado)
- `proto/asistencias.proto` (existente, mejorado)
- `proto/notificaciones.proto` (SendBienvenida, SendBaja, SendCierreMateria)
- `proto/reportes.proto` (GenerateReport, GetHistorialDocente)

**Verificación:**
```bash
bash scripts/generate_all_protos.sh
# → Todos compilan sin error ✅
```

---

## ISSUE-202 — Generación de Código y Servidor gRPC

| # | Tarea | Criterio | Estado |
|---|-------|----------|--------|
| 202.1 | `grpcio` en `requirements.txt` | Versiones fijadas (1.60+) | ✅ OK |
| 202.2 | Script `generate_proto.sh` | Apunta a `../../proto` o var env | ✅ OK |
| 202.3 | Política de `proto_generated/` | En `.gitignore` o versionado | ✅ OK (versionado) |
| 202.4 | Clase `*Servicer` sin NotImplementedError | Métodos implementados | ✅ OK |
| 202.5 | Arranque gRPC + REST en mismo contenedor | Gunicorn + hilo/proceso gRPC | ✅ OK |
| 202.6 | Puertos 50051–50057 exclusivos | Docker expone correctamente | ✅ OK |

**Archivos entregados:**
- `ms-*/generate_proto.sh` (scripts de compilación)
- `ms-*/proto_generated/` (stubs compilados)
- `ms-*/grpc_server/` (servicers implementados)
- `ms-*/entrypoint.sh` (lanza Gunicorn + gRPC)

**Verificación:**
```bash
docker compose up --build ms-alumnos ms-auth -d
docker compose logs ms-alumnos | grep "✓ Servidor gRPC"
# → Muestra que gRPC está listo en 50053 ✅
```

---

## ISSUE-203 — Clientes gRPC entre Microservicios

| # | Tarea | Criterio | Estado |
|---|-------|----------|--------|
| 203.1 | Inventario de dependencias | Tabla consumidor → proveedor | ✅ OK |
| 203.2 | Módulo `grpc_clients.py` | Canal singleton reutilizable | ✅ OK |
| 203.3 | Variables de entorno | MS_*_GRPC_HOST/PORT | ✅ OK |
| 203.4 | Timeout en cada call | 3–10 segundos | ✅ OK (5s default) |
| 203.5 | Mapeo de excepciones | gRPC StatusCode → Python exc | ✅ OK |
| 203.6 | Canal por proceso | Singleton lazy | ✅ OK |

**Pares Verificados (3+ requeridos):**

1. **ms-calificaciones → ms-alumnos**
   - Método: `GetAlumnoById`
   - Implementación: `ms-calificaciones/grpc_clients.py`
   - Test: `ms-calificaciones/tests/test_grpc_utils.py` ✅

2. **ms-asistencias → ms-alumnos**
   - Método: `GetAlumnoById`
   - Implementación: `ms-asistencias/grpc_clients.py`
   - Test: `ms-asistencias/tests/test_grpc_utils.py` ✅

3. **ms-calificaciones → ms-auth**
   - Método: `ValidateToken`
   - Implementación: `ms-calificaciones/grpc_clients.py`
   - Test: Mapeo de UNAUTHENTICATED ✅

**Adicionales (ya en repo):**
- ms-reportes → ms-alumnos, ms-periodos
- ms-notificaciones → ms-alumnos

**Verificación:**
```bash
docker compose exec ms-asistencias sh -lc "cd /app && python tests/test_grpc_utils.py"
# → Ran 2 tests ... OK ✅
```

---

## ISSUE-204 — Testing y Documentación

| # | Tarea | Criterio | Estado |
|---|-------|----------|--------|
| 204.1 | Instalar `grpcurl` | Documentado en comandos | ✅ OK |
| 204.2 | Scripts Python mínimos | `if __name__ == '__main__'` | ✅ OK |
| 204.3 | Manual técnico | Sección "Cómo probar gRPC" | ✅ OK |
| 204.4 | Errores propagados | Mapear a 401/403/404/502 | ✅ OK |

**Archivos entregados:**

- `scripts/grpc_smoke_tests.sh` — ejecuta pruebas en Docker
- `docs/PROTO_CLIENTS.md` — guía de prueba manual
- `docs/EPIC2_DOCUMENTACION/` — documentación completa (esta carpeta)
- `.github/workflows/grpc_smoke_tests.yml` — CI integration
- Tests unitarios con `unittest` en cada MS consumidor

**Verificación de Smoke Tests:**
```bash
bash scripts/grpc_smoke_tests.sh
# → Levanta servicios, ejecuta tests en contenedores, limpia ✅
```

**Verificación Manual (grpcurl):**
```bash
# Instalar grpcurl (si no está)
brew install grpcurl  # macOS / Linux
# Windows: descargar desde https://github.com/fullstorydev/grpcurl/releases

# Probar ms-alumnos
grpcurl -plaintext ms-alumnos:50053 proto.AlumnosService/GetAlumnoById -d '{"alumno_id":123}'
```

---

## Resumen de Estado

| Componente | Completitud | Nota |
|-----------|------------|------|
| Contratos `.proto` | 100% | 7/7 archivos |
| Generación stubs | 100% | Todos compilan |
| Servidores gRPC | 100% | 7 servicers implementados |
| Clientes gRPC | 100% | 3+ pares verificados |
| Error handling | 100% | Mapeo completo |
| Tests unitarios | 100% | 2+ servicios testeados |
| CI/CD | 100% | GitHub Actions integrado |
| Documentación | 100% | 6 archivos en EPIC2_DOCUMENTACION/ |

**Status General:** ✅ **COMPLETADO**

---

## Próximos Pasos (Futura)

- [ ] Añadir `grpc_health_probe` en CI avanzado
- [ ] Integrar mTLS en producción (evaluación)
- [ ] Aumentar cobertura de tests a 10+ pares
- [ ] Documentar patrones de metadata (JWT en headers)
