# Epic 2: Arquitectura y Comunicación gRPC — Documentación Completa

**Desarrollador:** Guillermo  
**Estado:** Completado  
**Fecha de entrega:** Mayo 18, 2026  
**Versión:** 1.0

---

## Descripción General

Esta carpeta contiene toda la documentación técnica, guías de implementación, comandos de prueba y estado de entrega de la **Epic 2: Arquitectura y Comunicación gRPC**.

La Epic 2 es transversal al proyecto AGM: define cómo los 7 microservicios se comunican entre sí usando gRPC, garantizando bajo acoplamiento, despliegue independiente y cumplimiento del requisito de evaluación (20% gRPC).

---

## Contenido de esta Carpeta

| Archivo | Propósito |
|---------|-----------|
| `00_README.md` | Este archivo; índice y descripción general |
| `01_ESTADO_IMPLEMENTACION.md` | Status de cada ISSUE (201-204) y criterios de aceptación |
| `02_MATRIZ_DEPENDENCIAS.md` | Matriz de pares MS consumidor → proveedor con métodos |
| `03_GUIA_COMANDOS_PRUEBA.md` | Comandos copy-paste para probar gRPC localmente |
| `04_ESTRUCTURA_ARCHIVOS.md` | Árbol de archivos entregados en cada MS |
| `05_CHECKLIST_SALIDA.md` | Checklist final de validación antes de release |
| `06_NOTAS_TECNICAS.md` | Decisiones técnicas, patrones y buenas prácticas usadas |

---

## Resumen Ejecutivo

### Qué se Implementó

✅ **7 contratos `.proto`** (uno por MS)  
✅ **Generación de stubs** vía scripts `generate_proto.sh`  
✅ **Servidores gRPC** en Django (puerto 50051–50057)  
✅ **Clientes gRPC** con canales singleton reutilizables  
✅ **Mapeo de errores** gRPC → excepciones Python  
✅ **Tests unitarios** para mapeo de errores  
✅ **Smoke tests** en CI y scripts de validación  
✅ **Documentación** técnica completa  

### Pares de MS Comunicándose (3+)

1. `ms-calificaciones` → `ms-alumnos` (`GetAlumnoById`)
2. `ms-asistencias` → `ms-alumnos` (`GetAlumnoById`)
3. `ms-calificaciones` → `ms-auth` (`ValidateToken`)

Adicionales ya en repo:
- `ms-reportes` → `ms-alumnos`, `ms-periodos`
- `ms-notificaciones` → múltiples MS

### Criterios de Aceptación Cumplidos

- [x] Los 7 `.proto` compilan sin errores
- [x] Cada MS con servidor gRPC escucha en puerto asignado
- [x] ≥3 pares de MS con llamadas verificadas
- [x] Todos los clientes con timeout y manejo de `RpcError`
- [x] Documentación en manual técnico + comandos de prueba
- [x] Ningún MS accede a BD de otro MS

---

## Cómo Usar Esta Documentación

1. **Para entender qué se hizo:** lee `01_ESTADO_IMPLEMENTACION.md`
2. **Para ver qué comunica con qué:** lee `02_MATRIZ_DEPENDENCIAS.md`
3. **Para probar localmente:** copia comandos de `03_GUIA_COMANDOS_PRUEBA.md`
4. **Para revisar antes de release:** usa `05_CHECKLIST_SALIDA.md`
5. **Para decisiones técnicas:** consult `06_NOTAS_TECNICAS.md`

---

## Quick Start — Probar Localmente

```bash
# Generar stubs
bash scripts/generate_all_protos.sh

# Levantar servicios
docker compose up --build ms-alumnos ms-auth ms-calificaciones ms-asistencias -d

# Esperar ~5s, luego ejecutar smoke tests
docker compose exec ms-calificaciones sh -lc "cd /app && PYTHONPATH=/app python tests/test_grpc_utils.py"
docker compose exec ms-asistencias sh -lc "cd /app && PYTHONPATH=/app python tests/test_grpc_utils.py"

# Limpieza
docker compose down
```

---

## Archivos Entregados por Módulo

### Proto (raíz monorepo)
- `proto/auth.proto` — servicios Auth
- `proto/periodos.proto` — servicios Periodos
- `proto/alumnos.proto` — servicios Alumnos
- `proto/calificaciones.proto` — servicios Calificaciones
- `proto/asistencias.proto` — servicios Asistencias
- `proto/notificaciones.proto` — servicios Notificaciones
- `proto/reportes.proto` — servicios Reportes

### Scripts (raíz)
- `scripts/generate_all_protos.sh` — compilar todos los protos
- `scripts/grpc_smoke_tests.sh` — ejecutar smoke tests en Docker
- `.github/workflows/grpc_smoke_tests.yml` — CI/CD para smoke tests

### Por Microservicio (ejemplo: ms-calificaciones)
- `ms-calificaciones/grpc_clients.py` — cliente gRPC con canales singleton
- `ms-calificaciones/grpc_utils.py` — mapeo de errores gRPC
- `ms-calificaciones/tests/test_grpc_utils.py` — tests unitarios
- `ms-calificaciones/scripts/test_calificaciones_client.py` — prueba manual

(Similar para `ms-asistencias` y otros MS)

---

## Estado de Validación

| Componente | Estado |
|-----------|--------|
| Compilación `.proto` | ✅ OK |
| Generación de stubs | ✅ OK |
| Servidores gRPC en Docker | ✅ OK |
| Clientes gRPC | ✅ OK |
| Tests unitarios (mapeo errores) | ✅ OK en ms-asistencias |
| Smoke tests CI | ✅ Configurado |
| Documentación | ✅ Esta carpeta |

---

## Referencias

- Plan de acción: `docs/devs/Guillermo/PLAN_ACCION_EPIC2_ARQUITECTURA_GRPC.md`
- Backlog: `docs/backlog_AGM_completo.md`
- Contexto global: `docs/CONTEXTO_GLOBAL_PROYECTO.md`
- Documento del proyecto: `docs/Proyecto_Final_SW_AGM.md`
