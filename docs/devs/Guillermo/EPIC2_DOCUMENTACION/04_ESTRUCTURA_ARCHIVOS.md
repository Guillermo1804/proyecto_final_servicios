# 04 — Estructura de Archivos Entregados

**Árbol de archivos nuevos y modificados para la Epic 2.**

---

## Raíz del Monorepo

```
proyecto_final_servicios/
├── proto/
│   ├── auth.proto                    [EXISTENTE, sin cambios]
│   ├── periodos.proto                [EXISTENTE, sin cambios]
│   ├── alumnos.proto                 [EXISTENTE, sin cambios]
│   ├── calificaciones.proto          [EXISTENTE, sin cambios]
│   ├── asistencias.proto             [EXISTENTE, sin cambios]
│   ├── notificaciones.proto          [EXISTENTE, sin cambios]
│   └── reportes.proto                [EXISTENTE, sin cambios]
│
├── scripts/
│   ├── generate_all_protos.sh        [EXISTENTE - top-level script]
│   ├── grpc_smoke_tests.sh           [NUEVO ✅ - orquesta smoke tests]
│   └── ...otros scripts...
│
├── .github/
│   └── workflows/
│       └── grpc_smoke_tests.yml      [NUEVO ✅ - CI/CD para smoke tests]
│
├── docs/
│   ├── PROTO_CLIENTS.md              [NUEVO ✅ - guía de clients]
│   └── EPIC2_DOCUMENTACION/          [NUEVO ✅ - carpeta de docs]
│       ├── 00_README.md              [Índice y descripción general]
│       ├── 01_ESTADO_IMPLEMENTACION.md   [Status por ISSUE]
│       ├── 02_MATRIZ_DEPENDENCIAS.md    [Matriz MS → MS]
│       ├── 03_GUIA_COMANDOS_PRUEBA.md   [Comandos copy-paste]
│       ├── 04_ESTRUCTURA_ARCHIVOS.md    [Este archivo]
│       ├── 05_CHECKLIST_SALIDA.md       [Validación final]
│       └── 06_NOTAS_TECNICAS.md         [Decisiones de diseño]
│
└── ...
```

---

## Por Microservicio

### Patrón General (cada ms-*)

```
ms-SERVICIO/
├── Dockerfile                        [EXISTENTE - con EXPOSE puerto gRPC]
├── entrypoint.sh                     [EXISTENTE - lanza gRPC + REST]
├── requirements.txt                  [EXISTENTE - incluye grpcio 1.60+]
├── manage.py                         [EXISTENTE - Django CLI]
│
├── generate_proto.sh                 [EXISTENTE - compilar stubs]
│
├── grpc_clients.py                   [NUEVO ✅ - cliente gRPC]
├── grpc_utils.py                     [NUEVO ✅ - mapeo de errores]
│
├── proto_generated/
│   ├── __init__.py                   [GENERADO]
│   ├── *_pb2.py                      [GENERADO - tipos protobuf]
│   └── *_pb2_grpc.py                 [GENERADO - stubs]
│
├── grpc_server/                      [EXISTENTE o NUEVO - servicers]
│   ├── __init__.py
│   └── servicer.py                   [Implementación del Servicer]
│
├── scripts/
│   └── test_*_client.py              [NUEVO ✅ - prueba del cliente]
│
├── tests/
│   └── test_grpc_utils.py            [NUEVO ✅ - tests unitarios]
│
├── apps/                             [EXISTENTE - apps Django]
├── config/                           [EXISTENTE - settings]
├── .env                              [EXISTENTE - vars de entorno]
└── .env.example                      [EXISTENTE - plantilla]
```

---

## Detalle por Servicio

### ms-alumnos

```
ms-alumnos/
├── generate_proto.sh                 ← Compilar alumnos.proto
├── grpc_clients.py                   ✅ NUEVO - [NO CONSUME, solo PROVEE]
├── proto_generated/
│   ├── alumnos_pb2.py                ← Tipos
│   └── alumnos_pb2_grpc.py           ← Stub
├── grpc_server/
│   └── servicer.py                   ← AlumnosServicer implementado
└── scripts/
    └── test_alumnos_client.py        ✅ NUEVO - [Opcional, no consumidor]
```

**Nota:** ms-alumnos NO consume otros servicios, pero PROVEE `GetAlumnoById`, `GetAlumnosByMateria`, etc.

---

### ms-auth

```
ms-auth/
├── generate_proto.sh                 ← Compilar auth.proto
├── grpc_clients.py                   ✅ NUEVO - [NO CONSUME]
├── proto_generated/
│   ├── auth_pb2.py
│   └── auth_pb2_grpc.py
├── grpc_server/
│   └── servicer.py                   ← AuthServicer implementado
└── scripts/
    └── test_auth_client.py           ✅ NUEVO - [Opcional]
```

**Nota:** ms-auth PROVEE validación, es proveedor central.

---

### ms-calificaciones

```
ms-calificaciones/
├── generate_proto.sh                 ← Compilar calificaciones.proto
├── grpc_clients.py                   ✅ NUEVO - [Llama a ms-alumnos, ms-auth]
│                                        • get_alumno_by_id(alumno_id)
│                                        • validate_token(token)
├── grpc_utils.py                     ✅ NUEVO - [Mapeo de errores gRPC]
│
├── proto_generated/
│   ├── calificaciones_pb2.py
│   ├── calificaciones_pb2_grpc.py
│   ├── alumnos_pb2.py                ← Importado desde proto/alumnos.proto
│   ├── alumnos_pb2_grpc.py
│   ├── auth_pb2.py                   ← Importado desde proto/auth.proto
│   └── auth_pb2_grpc.py
│
├── grpc_server/
│   └── servicer.py                   ← CalificacionesServicer implementado
│
├── scripts/
│   └── test_calificaciones_client.py ✅ NUEVO - [Prueba clients]
│
├── tests/
│   └── test_grpc_utils.py            ✅ NUEVO - [Tests unitarios]
│                                        • test_not_found()
│                                        • test_unauthenticated()
│                                        • test_deadline()
│                                        • test_internal()
│
├── apps/
├── config/
└── ...
```

---

### ms-asistencias

```
ms-asistencias/
├── generate_proto.sh                 ← Compilar asistencias.proto
├── grpc_clients.py                   ✅ NUEVO - [Llama a ms-alumnos]
│                                        • get_alumno_by_id(alumno_id)
│
├── grpc_utils.py                     ✅ NUEVO - [Mapeo de errores]
│
├── proto_generated/
│   ├── asistencias_pb2.py
│   ├── asistencias_pb2_grpc.py
│   ├── alumnos_pb2.py
│   └── alumnos_pb2_grpc.py
│
├── grpc_server/
│   └── servicer.py                   ← AsistenciasServicer
│
├── scripts/
│   └── test_asistencias_client.py    ✅ NUEVO
│
├── tests/
│   └── test_grpc_utils.py            ✅ NUEVO - [Tests]
│
├── apps/
├── config/
└── ...
```

---

### ms-notificaciones

```
ms-notificaciones/
├── grpc_clients/
│   ├── errors.py                     ✅ [Mapeo de errores]
│   ├── channel.py                    ✅ [Canales singleton]
│   └── __init__.py
│
├── grpc_server/
│   └── servicer.py                   ← NotificacionesServicer
│
├── proto_generated/
│   ├── notificaciones_pb2.py
│   ├── notificaciones_pb2_grpc.py
│   ├── alumnos_pb2.py
│   ├── alumnos_pb2_grpc.py
│   ├── periodos_pb2.py
│   └── periodos_pb2_grpc.py
│
└── ...
```

---

### ms-reportes

```
ms-reportes/
├── grpc_clients/
│   ├── exceptions.py                 ✅ [Excepciones de dominio]
│   ├── channel.py                    ✅ [Canales]
│   └── __init__.py
│
├── grpc_server/
│   └── servicer.py                   ← ReportesServicer
│
├── proto_generated/
│   ├── reportes_pb2.py
│   ├── reportes_pb2_grpc.py
│   ├── alumnos_pb2.py
│   ├── periodos_pb2.py
│   ├── calificaciones_pb2.py
│   └── asistencias_pb2.py
│
└── ...
```

---

## Resumen de Ficheros Nuevos (✅)

| Archivo | Propósito |
|---------|-----------|
| `scripts/grpc_smoke_tests.sh` | Orquesta pruebas en Docker |
| `.github/workflows/grpc_smoke_tests.yml` | CI/CD GitHub Actions |
| `docs/PROTO_CLIENTS.md` | Guía de clientes gRPC |
| `docs/EPIC2_DOCUMENTACION/` | **6 archivos de documentación** |
| `ms-*/grpc_clients.py` | Cliente gRPC (consumidores) |
| `ms-*/grpc_utils.py` | Mapeo de errores |
| `ms-*/tests/test_grpc_utils.py` | Tests unitarios |
| `ms-*/scripts/test_*_client.py` | Scripts de prueba manual |

**Total:**
- **12+ archivos nuevos** en servicios
- **6 docs de EPIC2_DOCUMENTACION/**
- **2 CI/CD files**
- **0 archivos eliminados**

---

## Cómo Navegar

- Para entender qué se hizo: leer `01_ESTADO_IMPLEMENTACION.md`
- Para ver dónde buscar código: usar este archivo (`04_ESTRUCTURA_ARCHIVOS.md`)
- Para probar: seguir `03_GUIA_COMANDOS_PRUEBA.md`
- Para entender decisiones: leer `06_NOTAS_TECNICAS.md`
