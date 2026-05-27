# Plan de acción — Epic 2: Arquitectura y Comunicación gRPC

**Desarrollador:** Guillermo  
**Alcance:** `docs/backlog_AGM_completo.md` — **Epic 2 (ISSUE-201 … ISSUE-204)**  
**Enunciado:** `docs/Proyecto_Final_SW_AGM.md` — §3 objetivo 2, §4.2 (gRPC obligatorio), §5.4.3 Comunicación gRPC, §7 criterio 20% gRPC  
**Contexto:** `docs/CONTEXTO_GLOBAL_PROYECTO.md` — §3 reglas, §5 mapa de llamadas, §6 patrones

---

## 1. Rol de esta épica en el proyecto

La Epic 2 es **transversal**: no entrega pantallas de usuario, pero **define y opera** el contrato por el cual los siete microservicios se comportan como sistema distribuido real. Si falla, el proyecto incurre en penalizaciones del enunciado (REST entre MS en lugar de gRPC, o “monolito disfrazado”).

| Objetivo | Cómo lo cubre esta épica |
|----------|---------------------------|
| Bajo acoplamiento entre MS | Contratos `.proto` estables; datos vía RPC, no SQL cruzado |
| Evaluación gRPC (20%) | `.proto` versionados, stubs generados, **≥3 pares** de MS comunicándose |
| Despliegue independiente | Cada MS expone su **puerto gRPC** fijo (50051–50057) en Docker |

---

## 2. Inventario de contratos (`/proto`)

Según **ISSUE-201**, deben existir y compilar **7 archivos** en la raíz del monorepo:

| Archivo | `package` / servicio | Puerto servidor |
|---------|----------------------|-------------------|
| `auth.proto` | Auth: `ValidateToken`, `GetUserById`, `CheckRole` | 50051 |
| `periodos.proto` | Periodos: `GetMateriaById`, `GetMateriasByDocente`, `GetPeriodoActivo` | 50052 |
| `alumnos.proto` | Alumnos: `GetAlumnosByMateria`, `GetAlumnoById`, `IsAlumnoEnMateria` (+ RPC extra si el repo ya los usa, p. ej. docente) | 50053 |
| `calificaciones.proto` | Ver `proto/calificaciones.proto` actual | 50054 |
| `asistencias.proto` | Ver `proto/asistencias.proto` actual | 50055 |
| `notificaciones.proto` | Notificaciones | 50056 |
| `reportes.proto` | Reportes | 50057 |

**Reglas proto3:** `syntax = "proto3";`, tipos explícitos, `repeated` para listas, sin valores por defecto en mensajes para campos requeridos (usar validación en código si hace falta).

---

## 3. Plan por issue (granular y a prueba de errores)

### ISSUE-201 — Definición de contratos `.proto`

| # | Tarea | Criterio de aceptación |
|---|--------|------------------------|
| 201.1 | Un `.proto` por servicio que **expone** gRPC (no mezclar dos MS en un solo archivo salvo convención explícita del repo) | Estructura alineada al backlog |
| 201.2 | Mensajes `Request`/`Response` por cada RPC | Sin ambigüedad en nombres de campos (`materia_id`, `alumno_id`, …) |
| 201.3 | Compilación global | Desde la raíz: `python -m grpc_tools.protoc -I./proto ...` sobre **los 7** sin error |
| 201.4 | Control de versiones | Cambios breaking → comunicar al equipo + bump documentado en README técnico |
| 201.5 | Coherencia con `CONTEXTO_GLOBAL_PROYECTO.md` §5 | Cada flecha del mapa tiene método correspondiente o está justificado |

**Errores frecuentes:** cambiar un campo y no regenerar stubs en **todos** los MS que importan ese proto; usar `optional` sin consenso del equipo (Python antiguo).

---

### ISSUE-202 — Generación de código y **servidor** gRPC en Django

| # | Tarea | Criterio |
|---|--------|----------|
| 202.1 | `grpcio` + `grpcio-tools` en `requirements.txt` de **cada** MS que implementa servidor | Versiones fijadas |
| 202.2 | Script `generate_proto.sh` (o `.ps1` en Windows) en cada MS | Ruta `-I` apunta al monorepo `../../proto` o variable `PROTO_ROOT` |
| 202.3 | Paquete generado (ej. `proto_generated/`) en `.gitignore` **o** versionado — **acordar una sola política** en el equipo | Evitar drift entre devs |
| 202.4 | Clase `*Servicer` que hereda del `*Servicer` generado e implementa cada `rpc` | Sin `NotImplementedError` en métodos usados en demo |
| 202.5 | Arranque del servidor gRPC junto al REST | Mismo contenedor: entrypoint lanza Gunicorn + hilo/proceso gRPC **o** `asyncio` en el mismo proceso según patrón del repo |
| 202.6 | Puertos exclusivos 50051–50057 | Tabla en README; `docker-compose` publica solo lo necesario |

**Errores frecuentes:** olvidar bindear `0.0.0.0` en Docker (solo `127.0.0.1`); doble bind al reiniciar hot-reload.

---

### ISSUE-203 — Clientes gRPC entre microservicios

| # | Tarea | Criterio |
|---|--------|----------|
| 203.1 | Inventario de dependencias | Tabla MS consumidor → MS proveedor → método (copiar de `CONTEXTO_GLOBAL` §5 y validar en código) |
| 203.2 | Módulo `grpc_clients.py` (o paquete `grpc_clients/`) por MS | Funciones del estilo `get_alumno_by_id(client, alumno_id)` con canal reutilizable |
| 203.3 | Variables de entorno | `MS_AUTH_GRPC_HOST`, `MS_AUTH_GRPC_PORT`, … sin URLs hardcodeadas |
| 203.4 | **Timeout** en cada `stub.Call` (p. ej. 3–10 s) | Nunca espera infinita |
| 203.5 | Mapeo de excepciones | `grpc.RpcError` → `StatusCode.NOT_FOUND`, `UNAUTHENTICATED`, `PERMISSION_DENIED`, `DEADLINE_EXCEEDED`, `INTERNAL` |
| 203.6 | Canal gRPC | Preferir **un canal por proceso** reutilizable (singleton lazy) en lugar de abrir canal por request sin cerrar |

**Criterio de evaluación del curso:** al menos **tres pares** distintos de MS con llamadas reales (ej. MS-4→MS-3, MS-5→MS-3, MS-3→MS-6). Documentar cuáles pares demostrarán en la presentación.

---

### ISSUE-204 — Testing y documentación de gRPC

| # | Tarea | Criterio |
|---|--------|----------|
| 204.1 | Instalar `grpcurl` (o `grpc_cli`) | Invocación manual documentada por cada RPC crítico |
| 204.2 | Scripts Python mínimos en `scripts/` o por MS | `if __name__ == "__main__"` que llama a un método y imprime respuesta |
| 204.3 | Manual técnico (Epic 11) | Sección “Cómo probar gRPC” con comandos copy-paste |
| 204.4 | Errores propagados | El MS consumidor no debe convertir cualquier fallo gRPC en 500 opaco; mapear a 401/403/404/502 según política |

**Prueba de estrés leve:** apagar un MS proveedor y verificar que el consumidor responde con timeout controlado, no deadlock del worker.

---

## 4. Matriz de dependencias gRPC (referencia rápida)

> Copiado del contexto global; Guillermo debe mantenerla actualizada si el equipo añade RPC.

| Consumidor | Proveedor | Ejemplo de método |
|------------|-----------|-------------------|
| MS-2,3,4,5 | MS-1 | `ValidateToken` |
| MS-2 | MS-3 | (si aplica importaciones) |
| MS-3 | MS-1, MS-6 | usuarios / notificaciones |
| MS-4 | MS-1, MS-2, MS-3, MS-6 | token, materia, alumnos, cierre |
| MS-5 | MS-1, MS-3 | token, alumno/materia |
| MS-6 | MS-2, MS-3 | materia, alumno |
| MS-7 | MS-1,2,3,4,5 | reportes y estadísticas |

---

## 5. Coordinación con Epic 1 (DevOps)

- Cada `Dockerfile` debe **EXPOSE** el puerto gRPC.  
- `docker-compose`: nombres de servicio = host en env (`ms-calificaciones`, etc.).  
- Healthcheck: puede ser solo HTTP; gRPC health opcional (`grpc_health_probe` en CI avanzado).

---

## 6. Seguridad

| Tema | Acción |
|------|--------|
| gRPC sin TLS interno | En Docker red privada suele bastar; en nube evaluar mTLS o mesh más adelante |
| Metadata | Si se pasa JWT por metadata `authorization`, documentar el mismo formato que REST |
| Reflexión | Deshabilitar en producción si no se usa (superficie de ataque) |

---

## 7. Checklist de salida Epic 2

- [ ] Los 7 `.proto` compilan sin errores.  
- [ ] Cada MS con servidor gRPC escucha en el puerto asignado dentro de Compose.  
- [ ] ≥3 pares de MS con llamadas verificadas (logs + grpcurl o script).  
- [ ] Todos los clientes con timeout y manejo de `RpcError`.  
- [ ] Documentación en manual técnico / README con comandos de prueba.  
- [ ] Ningún MS accede a la BD de otro MS (revisión de código + ORM).  

---

## 8. Referencias

- `docs/backlog_AGM_completo.md` — Epic 2  
- `docs/Proyecto_Final_SW_AGM.md` — §5.4.3  
- `docs/CONTEXTO_GLOBAL_PROYECTO.md` — §5  
- Carpeta `/proto/` del repositorio  
