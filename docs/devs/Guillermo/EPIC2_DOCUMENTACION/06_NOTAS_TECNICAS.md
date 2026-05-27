# 06 — Notas Técnicas: Decisiones de Diseño

**Por qué se hizo así y lecciones aprendidas.**

---

## I. Arquitectura de Canales (Singleton Lazy)

### Decisión
```python
# ms-calificaciones/grpc_clients.py

_channel_alumnos = None

def alumnos_channel():
    global _channel_alumnos
    if _channel_alumnos is None:
        _channel_alumnos = grpc.insecure_channel(
            host_port, 
            options=[...],
            compression=grpc.Compression.Gzip
        )
    return _channel_alumnos
```

### Justificación
1. **Reutilización:** Un canal maneja múltiples RPCs, no crear channel por RPC
2. **Lazy initialization:** Solo conectar cuando se necesite (primer uso)
3. **Global state:** Necesario porque gRPC channels son thread-safe y costosas de crear
4. **No es anti-pattern:** es recomendado por gRPC docs para aplicaciones de larga duración

### Alternativa Rechazada
- Inyección de dependencia (DI container): Complejidad en Django, no necesario en monorepo
- Conexión en startup: Fallaría si el proveedor aún no está listo (timing issue en Docker)

---

## II. Timeout Fijo (5 segundos por defecto)

### Decisión
```python
def get_alumno_by_id(alumno_id, timeout=None):
    timeout = timeout or config('GRPC_CALL_TIMEOUT', default=5, cast=int)
    stub = proto_generated.alumnos_pb2_grpc.AlumnosServiceStub(channel)
    response = stub.GetAlumnoById(
        proto_generated.alumnos_pb2.GetAlumnoByIdRequest(alumno_id=alumno_id),
        timeout=timeout
    )
```

### Justificación
1. **Sensible por defecto:** 5s cubre la mayoría de BD queries en Docker local
2. **Configurable:** Permite override para operaciones largas (reportes = 30s)
3. **Previene bloqueo:** Si proveedor falla, no esperar indefinidamente
4. **Refleja SLA:** En producción, esto sería parte de SLA con el proveedor

### Valores Recomendados
| Caso | Timeout |
|------|---------|
| Queries simples (GetAlumnoById) | 5s |
| Bulk operations (GetAlumnosByMateria) | 15s |
| Reportes/análisis | 30–60s |

### Monitoreo Recomendado
En producción: instrumentar con `grpc_python_helloworld` y métricas de Prometheus
- `grpc_server_unary_latency_seconds` (lado servidor)
- `grpc_client_unary_latency_seconds` (lado cliente)

---

## III. Mapeo de Errores a Excepciones Python

### Decisión
```python
# ms-calificaciones/grpc_utils.py
def map_grpc_error(exc: grpc.RpcError) -> Exception:
    code = exc.code()
    if code == StatusCode.NOT_FOUND:
        return LookupError(f"NOT_FOUND: {exc.details()}")
    elif code == StatusCode.UNAUTHENTICATED:
        return PermissionError(f"UNAUTHENTICATED: {exc.details()}")
    # ... más casos
    return RuntimeError(...)
```

### Justificación
1. **Abstracción:** Código de aplicación no conoce detalles de gRPC
2. **Mantenibilidad:** Cambiar transport (gRPC → HTTP API) no requiere cambiar vistas
3. **Pythonic:** Usar excepciones estándar, no enums de gRPC
4. **Testing:** Fácil de mockear: `raise FakeRpcError(StatusCode.NOT_FOUND)`

### Mapeo Elegido
| StatusCode gRPC | Excepción Python | HTTP (si fuera REST) |
|-----------------|------------------|---------------------|
| `NOT_FOUND` | `LookupError` | 404 |
| `UNAUTHENTICATED` | `PermissionError` | 401 |
| `PERMISSION_DENIED` | `PermissionError` | 403 |
| `DEADLINE_EXCEEDED` | `TimeoutError` | 504 |
| Otros | `RuntimeError` | 500 |

### Alternativa Rechazada
- Propagar `grpc.RpcError` directamente: Mancharía toda la aplicación con imports de gRPC

---

## IV. Compilación de Protos: Centralizada vs. Per-Service

### Decisión: Centralizada
```bash
# scripts/generate_all_protos.sh
for proto_file in proto/*.proto; do
    name=$(basename $proto_file .proto)
    mkdir -p ms-$name/proto_generated
    python -m grpc_tools.protoc ...
done
```

### Justificación
1. **Single Source of Truth:** `.proto` files están en `proto/`, no duplicados
2. **Consistent Versions:** Todos los servicios usan misma versión de grpc-tools
3. **CI/CD Simple:** Una línea en workflow genera todos los stubs
4. **Versionado:** Stubs generados están en `.gitignore` o en repo (decisión del equipo)

### Alternativa Rechazada
- Per-service: Cada MS compile su propio `.proto`
  - Pro: Independencia de versiones
  - Con: Duplicación, complejidad, inconsistencia

---

## V. Insecure Channels (sin TLS)

### Decisión
```python
grpc.insecure_channel(host_port)  # No TLS en desarrollo
```

### Justificación
1. **Red Privada:** Docker bridge network (`agm-network`), no accesible desde fuera
2. **Desarrollo Local:** Evita overhead de certificados
3. **Testing:** Simplifica CI/CD (no necesita secret management)
4. **Performance:** Gzip compression provee algo de protección

### Para Producción
```python
# Pseudocódigo futuro
if os.getenv("GRPC_TLS_ENABLED") == "true":
    credentials = grpc.ssl_channel_credentials(
        root_certificates=os.getenv("GRPC_ROOT_CERT")
    )
    channel = grpc.secure_channel(host_port, credentials)
else:
    channel = grpc.insecure_channel(host_port)
```

---

## VI. Proto3 vs Proto2

### Decisión: Proto3
```protobuf
syntax = "proto3";

message GetAlumnoByIdRequest {
    int32 alumno_id = 1;
}
```

### Justificación
1. **Moderno:** Proto3 es estándar desde 2016
2. **Backward-compatible:** gRPC comunidad asume proto3
3. **Menores:** Implicit defaults (int=0, string=""), no obligatoria presencia de campos
4. **Simplificidad:** Menos verbosidad que proto2

### Implicación
- Campo no enviado ≠ error; se interpreta como default (0 o "")
- Para validación strict: usar `oneof` o validator custom en servidor

---

## VII. Puertos Dedicados (50051–50057)

### Decisión
```
MS     | gRPC Port | REST Port | BD Port
-------|-----------|-----------|--------
Auth   | 50051     | 8000      | 3306
Periodos | 50052   | 8001      | 3306
Alumnos | 50053    | 8002      | 3306
Calificaciones | 50054 | 8003 | 3306
Asistencias | 50055 | 8004    | 3306
Notificaciones | 50056 | 8005 | 3306
Reportes | 50057   | 8006     | 3306
```

### Justificación
1. **No conflictos:** Rango 50051–50057 no usado por servicios comunes
2. **Fácil recordar:** +1 por cada MS
3. **Separación:** gRPC y REST no compiten por puerto
4. **Documentable:** Tabla pequeña para memorizar

---

## VIII. Environment Variables: `MS_*_GRPC_HOST/PORT`

### Decisión
```python
GRPC_HOST = config('MS_ALUMNOS_GRPC_HOST', default='ms-alumnos')
GRPC_PORT = config('MS_ALUMNOS_GRPC_PORT', default=50053, cast=int)
```

### Justificación
1. **Docker Compose:** En `.env` global, fácil cambiar en desarrollo
2. **Kubernetes Ready:** Mismo patrón funciona con inyección de env vars de K8s
3. **Pruebas:** Permite redireccionar a localhost o servicio mock
4. **Seguridad:** No hardcodear direcciones en código

### Ejemplo `.env`
```env
MS_ALUMNOS_GRPC_HOST=ms-alumnos
MS_ALUMNOS_GRPC_PORT=50053
MS_AUTH_GRPC_HOST=ms-auth
MS_AUTH_GRPC_PORT=50051
GRPC_CALL_TIMEOUT=5
```

---

## IX. Testing: FakeRpcError Mock

### Decisión
```python
# ms-calificaciones/tests/test_grpc_utils.py
class FakeRpcError(grpc.RpcError):
    def __init__(self, code):
        self._code = code
    
    def code(self):
        return self._code
    
    def details(self):
        return f"Mock error: {self._code}"

def test_not_found():
    exc = FakeRpcError(StatusCode.NOT_FOUND)
    result = map_grpc_error(exc)
    assert isinstance(result, LookupError)
```

### Justificación
1. **Unit Tests:** No requieren Docker/servicios reales
2. **Rápido:** Se ejecutan en < 1 segundo localmente
3. **Determinista:** No depende de estado externo
4. **Simple:** Mockeamos solo lo necesario (`.code()` y `.details()`)

### Alternativa Rechazada
- Integration tests con servicios reales: más lento, CI/CD más complejo, pero también recomendado después (de smoke tests)

---

## X. Smoke Tests vs Unit Tests vs Integration Tests

### Decisión: 3 Niveles

```
Unit (ms-calificaciones/tests/test_grpc_utils.py)
├─ Rápido: < 1s
├─ Aislado: Mocks
└─ Ejecuta: pytest o unittest

Smoke (scripts/grpc_smoke_tests.sh)
├─ Rápido: 10–15s
├─ Real: Docker up + real connection
└─ Verifica: "servicios hablan entre sí"

Integration (manual, no automatizado aún)
├─ Lento: 30–60s
├─ Real: Full stack + datos
└─ Verifica: "flujos de negocio completos"
```

### Justificación
1. **Unit:** Rápido feedback en desarrollo local
2. **Smoke:** Verifica integración básica pre-deployment
3. **Integration:** Manual o separado, más costoso

### Próximos Pasos Recomendados
- Agregar pytest fixtures para tests de integración
- Implementar datos de prueba (factories)
- Documentar cómo ejecutar tests full-stack

---

## XI. gRPC Streaming (No Implementado)

### Decisión: Unary RPC solamente
```protobuf
service AlumnosService {
    rpc GetAlumnoById(GetAlumnoByIdRequest) returns (Alumno);
    // Nota: NOT implementado: rpc GetAlumnosByMateria(...) returns (stream Alumno);
}
```

### Justificación
1. **Scope:** Epic 2 cubre básicos (unary)
2. **Complejidad:** Streaming requiere manejo de context, canal abierto, timeout diferente
3. **Caso de uso:** GetAlumnosByMateria devuelve lista completa en 1 mensaje (OK por ahora)
4. **Futuro:** Si MateriaBatch > 1000 alumnos, revisar streaming

### Cuándo Agregar Streaming
- Si query devuelve > 10K registros
- Si cliente necesita procesar resultados mientras llegan
- Después de profiling que muestre overhead

---

## XII. gRPC Interceptors (No Implementado)

### Decisión: Sin interceptors por ahora
```python
# No hay:
# - Logging interceptor
# - Metrics interceptor
# - Auth interceptor
```

### Justificación
1. **Scope:** Epic 2 es PoC, no producción
2. **Complejidad:** Interceptors requieren understand de gRPC internals
3. **Monitoreo:** Por ahora, logs de Django + manual debugging suficiente

### Para Producción
```python
# Pseudocódigo futuro
from prometheus_client import Counter
grpc_requests = Counter('grpc_requests_total', 'Total gRPC requests')

class MetricsInterceptor(grpc.UnaryClientInterceptor):
    def intercept_unary_unary(self, continuation, client_call_details, request):
        grpc_requests.inc()
        return continuation(client_call_details, request)

# Usar: channel = grpc.insecure_channel(..., interceptors=[MetricsInterceptor()])
```

---

## XIII. .proto Versioning

### Decisión: Sin versionamiento explícito
```protobuf
syntax = "proto3";
package proto;

message Alumno {
    int32 id = 1;
    string nombre = 2;
    // Futuro: string email = 3;
}
```

### Justificación
1. **Proto3 forward-compatible:** Nuevo campo (3) no rompe cliente viejo
2. **Monorepo:** Todos actualizar juntos (no multiple consumer versions)
3. **Simplificidad:** No necesitar v1.proto, v2.proto, etc.

### Si Fuera Multi-Repo
Necesitaríamos versionamiento:
```protobuf
// alumnos/v1/service.proto
syntax = "proto3";
package proto.alumnos.v1;
```

---

## XIV. Lessons Learned

### ✅ Lo que Funcionó Bien
1. **Centralizar `.proto`** → reduce duplicación
2. **Singleton channels** → eficiente, simple
3. **Error mapping** → limpia la aplicación
4. **Docker Compose** → desarrollo local fácil
5. **Smoke tests** → validación pre-commit

### ⚠️ Lo que Fue Difícil
1. **Docker imports** → Inicialmente confundió módulos en venv vs contenedor
   - **Solución:** Usar `sys.path.append()` en tests, o ejecutar con `python -m`
2. **Timing en tests** → Servicios no listos inmediatamente tras `up`
   - **Solución:** Healthchecks en compose, esperar 5–8s en scripts
3. **gRPC reflection** → Requiere setup adicional (no incluido aún)
   - **Futuro:** Agregar `grpcurl describe` o gRPC UI

### 🎯 Recomendaciones Futuras
1. **Monitoreo:** Instrumentar con Prometheus + Grafana
2. **Load Testing:** wrk o ghz para gRPC
3. **Multi-tenancy:** Considerar si múltiples clientes externos
4. **gRPC Gateway:** Exponer REST en paralelo (para clientes que no soportan gRPC)
5. **Documentación Automática:** Generar OpenAPI de .proto

---

## XV. Referencias

- [gRPC Python Docs](https://grpc.io/docs/languages/python/)
- [Protocol Buffers Guide](https://developers.google.com/protocol-buffers/docs/pythontutorial)
- [gRPC Best Practices](https://grpc.io/docs/guides/performance-best-practices/)
- [Django + gRPC Patterns](https://github.com/grpc-ecosystem/go-grpc-middleware) (referencia Go, pero conceptos aplican)

---

**Fin de Notas Técnicas**
