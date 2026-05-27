# gRPC Clients and Smoke Tests

This document explains how to test the gRPC clients implemented in the microservices and run smoke tests.

Services / pairs covered by the smoke tests
- `ms-calificaciones` -> `ms-alumnos` (`GetAlumnoById`)
- `ms-asistencias` -> `ms-alumnos` (`GetAlumnoById`)
- `ms-calificaciones` -> `ms-auth` (`ValidateToken`)

Quick commands

1) Generate stubs (if you changed `.proto`):

```bash
bash scripts/generate_all_protos.sh
```

2) Build and run services used by smoke tests:

```bash
docker compose up --build ms-alumnos ms-auth ms-calificaciones ms-asistencias -d
```

3) Run the top-level smoke test script (invokes the per-service Python test scripts inside containers):

```bash
bash scripts/grpc_smoke_tests.sh
```

Direct grpcurl examples (requires `grpcurl` on host):

```bash
# Get alumno by id (ms-alumnos)
grpcurl -plaintext ms-alumnos:50053 proto.AlumnosService/GetAlumnoById -d '{"alumno_id":123}'

# Validate token (ms-auth)
grpcurl -plaintext ms-auth:50051 proto.AuthService/ValidateToken -d '{"token":"<JWT>"}'
```

Interpreting results and common errors
- If a call fails with `UNAUTHENTICATED` or `PERMISSION_DENIED`, ensure JWTs are provided via metadata or the test uses allowed tokens.
- `DEADLINE_EXCEEDED` indicates timeout; increase `GRPC_CALL_TIMEOUT` or check network/connectivity.
- `NOT_FOUND` maps to 404 in HTTP semantics; tests currently raise `LookupError` when appropriate.

Environment variables used by clients
- `MS_ALUMNOS_GRPC_HOST`, `MS_ALUMNOS_GRPC_PORT` — host and port for `ms-alumnos` (defaults: `ms-alumnos:50053`).
- `MS_AUTH_GRPC_HOST`, `MS_AUTH_GRPC_PORT` — host and port for `ms-auth` (defaults: `ms-auth:50051`).
- `GRPC_CALL_TIMEOUT` — default per-call timeout in seconds (defaults: `5`).

Next steps
- Add `grpc_health_probe` checks or HTTP health endpoints that reflect gRPC health.
- Add CI job that runs `bash scripts/grpc_smoke_tests.sh` after `docker compose up --build`.
