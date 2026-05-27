# EPIC 6 — MS-4 Calificaciones & Ponderaciones

Versión detallada — Documentación técnica y operativa

Ruta del microservicio: `ms-calificaciones/`
Puertos: REST `8004`, gRPC `50054`
Base de datos: MySQL `agm_calificaciones_db` (servicio `db-calificaciones` en `docker-compose.yml`)

Contenido de este documento
- Visión general y arquitectura
- Modelos y reglas de negocio
- API REST (endpoints, métodos, payloads, ejemplos)
- gRPC (protos, stubs, servidor)
- Motor de cálculo (fórmulas, redondeo, consideraciones numéricas)
- Pruebas (unitarias y cómo ejecutarlas en Docker)
- Despliegue local con Docker (comandos y pasos)
- Troubleshooting habitual y soluciones
- Pasos siguientes y recomendaciones

--------------------------------------------------------------------------------

1) Visión general y arquitectura
--------------------------------
MS-4 es la fuente de verdad para ponderaciones, actividades y calificaciones. Expone una API REST y un servidor gRPC para consumo interno.

- Comunicación entre microservicios: gRPC (clientes en `grpc_clients/` usando stubs en `proto_generated/`).
- Autenticación y autorización: validación de token vía MS-1 (`validate_token`) y verificación de titularidad de materia vía MS-2 (`get_materia_by_id`).

Arquitectura de operaciones clave:
- Lectura del concentrado: datos locales + llamada a MS-3 para obtener nombres/matrículas.
- Cierre de materia: marca `cerrada=True` y notifica a MS-6 (`send_cierre_materia`); imprimir lista marca `lista_impresa=True` y bloquea ediciones.

--------------------------------------------------------------------------------

2) Modelos y reglas de negocio (ubicados en `apps/core/models.py`)
----------------------------------------------------------------

- `Ponderacion`
  - `materia_id` (IntegerField, index)
  - `nombre_categoria` (CharField(100))
  - `porcentaje` (DecimalField, max_digits=5, decimal_places=2)
  - Restricción: `unique_together` (`materia_id`, `nombre_categoria`)
  - Regla crítica: la suma de `porcentaje` por `materia_id` debe ser exactamente `100.00`.

- `Actividad`
  - `ponderacion` (FK a `Ponderacion`) — la `Actividad` pertenece a la misma `materia_id` que su `Ponderacion`.
  - `nombre`, `descripcion`, `fecha`
  - Restricción: no eliminar actividad si tiene `Calificacion` asociada.

- `Calificacion`
  - `actividad` (FK)
  - `alumno_id` (IntegerField, index)
  - `calificacion` (DecimalField max_digits=4, decimal_places=2) — rango 0.00–10.00
  - `unique_together` (`actividad`, `alumno_id`)
  - Operación: `POST /calificaciones` realiza upsert (`update_or_create`).

- `EstadoMateria`
  - `materia_id` (unique)
  - `cerrada` (bool)
  - `lista_impresa` (bool) — cuando `True` bloquea PUT/POST de calificaciones
  - `fecha_cierre`, `notificacion_enviada`

--------------------------------------------------------------------------------

3) API REST (endpoints principales — implementados en `apps/core/views.py`)
---------------------------------------------------------------------

Autorización: todas las rutas que modifican datos llaman `_authorize_materia_management(request, materia_id)` — valida token en MS-1 y confirma docente titular en MS-2.

Lista de endpoints (con ejemplos resumidos)

- GET /ponderaciones/<materia_id>
  - Uso: obtener lista de ponderaciones.
  - Respuesta (éxito): { success: true, data: { materia_id, ponderaciones: [...], total: "100.00" }, message }

- POST /ponderaciones/<materia_id>
  - Body: { "ponderaciones": [ { "nombre_categoria": "Exámenes", "porcentaje": "40.00" }, ... ] }
  - Validación: suma de porcentajes == 100.00; nombres únicos (case-insensitive).

- POST /ponderaciones/<materia_id>/importar
  - Multipart/form-data: archivo Excel en campo `archivo`.
  - El parser intenta mapear encabezados comunes (`nombre_categoria`, `porcentaje`, `peso`).

- POST /actividades
  - Body: { "ponderacion_id": <id>, "nombre": "Examen 1", "descripcion": "", "fecha": "YYYY-MM-DD" }
  - Verifica que la `ponderacion` exista y que pertenezca a la materia gestionada.

- GET /actividades?materia=<id>
  - Agrupa actividades por categoría (nombre, porcentaje, actividades[]).

- PUT /actividades/<id>, DELETE /actividades/<id>
  - DELETE devuelve 409 si la actividad tiene calificaciones.

- POST /calificaciones
  - Body: { "actividad_id": <id>, "alumno_id": <id>, "calificacion": "8.50" }
  - Upsert: crea o actualiza (unique constraint).
  - Requiere que `is_alumno_en_materia(alumno_id, materia_id)` sea verdadero.
  - Bloqueado si `EstadoMateria.lista_impresa=True`.

- POST /calificaciones/importar/<materia_id>
  - Excel con columnas: `matricula`/`alumno_id`, `actividad_id`, `calificacion`.
  - Resultado: resumen procesadas/importadas/fallos con lista de errores por fila.

- GET /concentrado/<materia_id>
  - Genera el concentrado: categorías (con actividades) y lista de alumnos con calificaciones, promedio_real y promedio_redondeado.
  - Combina `obtener_concentrado_materia` (datos locales) y `get_alumnos_by_materia` (MS-3) para completar nombres/matrículas.

- POST /materias/<id>/cerrar
  - Marca `cerrada=True`, `fecha_cierre=now()` y llama `send_cierre_materia(materia_id)` a MS-6.
  - Si la notificación falla, `notificacion_enviada` queda `False` — considerar reintentos externos.

- POST /materias/<id>/imprimir-lista
  - Nuevo endpoint: marca `lista_impresa=True` (bloqueo duro para ediciones de calificaciones).

Ejemplo rápido (crear ponderaciones):

curl -X POST http://localhost:8004/ponderaciones/10 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"ponderaciones": [{"nombre_categoria":"Examenes","porcentaje":"40.00"},{"nombre_categoria":"Tareas","porcentaje":"60.00"}]}'

Nota: las llamadas requieren un token válido emitido por MS-1 en entornos reales.

--------------------------------------------------------------------------------

4) gRPC
---------

- Protos: `proto/calificaciones.proto` — generar stubs con `grpcio-tools` si se actualiza el proto.
- Stubs generados: `ms-calificaciones/proto_generated/calificaciones_pb2.py` y `_pb2_grpc.py`.
- Servidor: `apps/core/management/commands/grpc_server.py` arranca el servidor en el puerto `GRPC_PORT` (`50054` por defecto).
- Implementación de RPCs: `grpc_server/servicer.py` implementa:
  - `GetConcentrado(GetConcentradoRequest) -> ConcentradoResponse`
  - `GetPromedioAlumno(PromedioRequest) -> PromedioResponse`
  - `GetEstadisticasMateria(EstadisticasRequest) -> EstadisticasMateriaResponse`

Consideraciones:
- Los RPCs usan el mismo motor de cálculo (`apps/core/services.py`) para asegurar consistencia REST ↔ gRPC.

--------------------------------------------------------------------------------

5) Motor de cálculo (precisión y reglas)
----------------------------------------

- Implementado en `apps/core/services.py`.
- Fórmula resumen:
  - Para cada `Ponderacion` c con porcentaje `p_c` (%): calcular promedio de las calificaciones del alumno sobre las actividades de esa categoría: \(\bar{g}_c\).
  - Contribución: \(\bar{g}_c \times (p_c / 100)\).
  - Promedio real = suma de contribuciones.

- Redondeo institucional (`redondear_institucional`):
  - Usar `Decimal` para evitar errores de float.
  - `parte_entera = floor(promedio_real)`; `fraccion = promedio_real - parte_entera`.
  - Si `fraccion >= 0.5` → `ceil`, en otro caso `floor`.

Tests obligatorios (ejemplos): `7.5 -> 8`, `7.4 -> 7`, `6.0 -> 6`, `10.0 -> 10`, `X.499999` vs `X.5`.

--------------------------------------------------------------------------------

6) Pruebas
-----------

- Unit tests: `ms-calificaciones/apps/core/tests.py`.
  - Cubre creación/listado de actividades, ponderaciones, importación, cálculos y bloqueo de ediciones.

- Ejecutar tests localmente dentro del contenedor Docker del MS:

```bash
docker compose up -d db-calificaciones ms-calificaciones
docker compose exec ms-calificaciones python manage.py test --verbosity=2
```

- Resultado observado en ejecución: `23 tests` — todos pasaron en mi verificación.

--------------------------------------------------------------------------------

7) Despliegue local con Docker
-------------------------------

Archivos relevantes: `docker-compose.yml`, cada microservicio tiene su propio `Dockerfile` y `.env`.

Pasos mínimos para desarrollo local:

1. Copiar `.env.example` a cada `ms-*/.env` y ajustar variables (si necesario).
2. Levantar servicios necesarios (bases de datos y microservicios):

```bash
docker compose up -d db-calificaciones ms-calificaciones
```

3. Verificar salud:

```bash
docker compose ps
curl -sS http://127.0.0.1:8004/health/
```

4. Para pruebas de integración levantar dependencias: `db-auth`, `ms-auth`, `db-periodos`, `ms-periodos`, `db-alumnos`, `ms-alumnos`, `db-notificaciones`, `ms-notificaciones`.

Nota sobre entornos Docker: el contenedor `ms-calificaciones` usa variables `MS_*_GRPC_HOST` para resolver nombres de los otros contenedores (ej. `ms-auth`, `ms-periodos`).

--------------------------------------------------------------------------------

8) Troubleshooting (errores comunes y soluciones)
------------------------------------------------

- Error: "Token inválido o expirado" en `_authorize_materia_management`
  - Causa: token faltante o MS-1 no disponible.
  - Solución: verificar header `Authorization`, arrancar `ms-auth` y confirmar endpoint `/health/`, revisar logs de `ms-auth`.

- Error: "La materia no existe." al crear/editar recursos
  - Causa: MS-2 (`ms-periodos`) no devolvió la materia.
  - Solución: arrancar `ms-periodos`, o en pruebas unitarias mockear `get_materia_by_id`.

- Error: gRPC `NOT_FOUND` desde `grpc_clients`
  - Causa: servicio destino no tiene datos locales o proto mismatch.
  - Solución: confirmar stubs regenerados con `python -m grpc_tools.protoc -I../proto --python_out=./proto_generated --grpc_python_out=./proto_generated ../proto/<service>.proto` y desplegar servicio destino.

- Error: migraciones ausentes / tablas no creadas
  - Comando: `docker compose exec ms-calificaciones python manage.py migrate` (ejecutar dentro del contenedor conectado a `db-calificaciones`).

- Error: importación Excel falla por encabezados
  - Comprobar encabezados esperados (la función intenta mapear `nombre_categoria`, `categoria`, `nombre` y `porcentaje`/`peso`).

- Error: operaciones bloqueadas por `lista_impresa`
  - Verificar `EstadoMateria` en BD: `SELECT * FROM apps_estadomateria WHERE materia_id = <id>`; si `lista_impresa=1`, se deben habilitar políticas administrativas o revertir manualmente para pruebas.

Logs y comandos útiles:

```bash
docker compose logs ms-calificaciones --follow
docker compose exec ms-calificaciones python manage.py showmigrations
docker compose exec ms-calificaciones python manage.py migrate --plan
```

--------------------------------------------------------------------------------

9) Pasos siguientes y recomendaciones
------------------------------------

- Ejecutar pruebas de integración end-to-end con los servicios reales (ms-auth, ms-periodos, ms-alumnos, ms-notificaciones) en Docker y crear un conjunto de scripts Postman/collection para flujos: ponderaciones → actividades → calificaciones → concentrado → cerrar → imprimir lista.
- Añadir reintentos y/o colas (ej. RabbitMQ) para la notificación de cierre si se requiere durabilidad en `send_cierre_materia`.
- Documentar contratos proto y mantener generación de stubs automatizada en CI.

--------------------------------------------------------------------------------

Anexos / Recursos rápidos
- Código fuente relevante: `ms-calificaciones/apps/core/` (models, views, serializers, services, tests)
- Stubs gRPC: `ms-calificaciones/proto_generated/`
- Docker: `docker-compose.yml`

Documento generado: `EPIC6_MS4_CALIFICACIONES_DOC.md`

