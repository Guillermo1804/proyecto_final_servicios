# Plan de accion - Bus de eventos y desacoplo entre microservicios AGM

**Objetivo general:** transformar la comunicacion entre microservicios AGM desde un esquema de llamadas directas sincrónicas a una arquitectura orientada a eventos con bus de mensajeria, tolerante a fallos, asincrona y sin dependencias estrictas entre servicios.

**Alcance:** MS-1 Auth & Users, MS-2 Periodos & Materias, MS-3 Docentes & Alumnos, MS-4 Calificaciones, MS-5 Asistencias QR, MS-6 Notificaciones, MS-7 Reportes & Stats, mas la infraestructura transversal del proyecto.

**Contexto arquitectonico actual:** el repositorio define gRPC como medio inter-MS, pero en la practica eso sigue siendo RPC sincrono request/response. Ese modelo protege parcialmente los requests con timeouts y fallbacks, pero no garantiza desacoplo ni entrega durable cuando un servicio cae. Este plan corrige esa limitacion.

---

## 1. Meta tecnica

### 1.1 Problema a resolver

Hoy varios flujos dependen de respuestas inmediatas de otros MS:
- validacion de JWT contra MS-1 en tiempo de request;
- notificaciones disparadas desde MS-3 y MS-4 hacia MS-6;
- reportes que consultan datos de MS-2, MS-3, MS-4 y MS-5 en caliente;
- lectura de datos de otros servicios para completar operaciones de negocio.

Eso crea dependencias encadenadas. Si un MS cae, otros degradan o fallan.

### 1.2 Objetivo de diseño

1. Cada microservicio debe ser capaz de completar su propia transaccion local sin bloquearse por disponibilidad de otros.
2. Las integraciones entre servicios deben ocurrir por eventos publicados en un bus durable.
3. Los consumidores deben ser idempotentes, reintentables y con cola de errores.
4. Las consultas puntuales que realmente requieran respuesta inmediata pueden seguir por gRPC, pero no deben formar parte del flujo critico de negocio.
5. Ningun microservicio debe leer la base de datos de otro.

### 1.3 Bus recomendado

**Recomendacion:** `RabbitMQ` como bus de eventos del sistema.

Motivos:
- encaja bien con Django y Python;
- permite `topic exchanges`, colas durables, `ack`, `nack`, reintentos, `dead-letter queues` y `TTL`;
- es mas simple de operar que Kafka para este tamano de proyecto;
- permite evolucionar a un modelo de eventos con muy poca friccion.

**Uso de Celery:** solo para ejecucion de workers y tareas asíncronas internas si el equipo ya lo domina. No debe confundirse con el bus de dominio.

### 1.4 Contrato de evento

Todo evento deberia usar un sobre comun versionado.

```json
{
  "event_id": "uuid",
  "event_name": "alumno.importado.v1",
  "event_version": 1,
  "aggregate_type": "alumno",
  "aggregate_id": "123",
  "source_service": "ms-alumnos",
  "correlation_id": "uuid",
  "causation_id": "uuid",
  "occurred_at": "2026-05-22T12:00:00Z",
  "payload": {}
}
```

### 1.5 Reglas de mensajeria

- Publicar solo despues de confirmar la transaccion local.
- Persistir eventos en una tabla `outbox` dentro de la misma BD del servicio productor.
- Consumir con `inbox` o tabla de idempotencia para evitar duplicados.
- Reintentar con backoff exponencial.
- Enviar a `DLQ` despues de N fallos.
- Incluir `correlation_id` y `causation_id` en todos los mensajes.
- Versionar contratos de evento como `*.v1`, `*.v2`, etc.

---

## 2. Cambios transversales a nivel proyecto

### Fase G0 - Fundacion del bus y estandar comun

**Objetivo:** dejar lista la infraestructura y los contratos compartidos antes de mover logica de negocio.

#### G0.1 Infraestructura

- Agregar un servicio `rabbitmq` al `docker-compose.yml` con volumen persistente, healthcheck y red interna.
- Configurar credenciales y vhost propios para AGM.
- Definir colas durables por dominio y colas de reintento/DLQ.
- Documentar variables de entorno comunes:
  - `RABBITMQ_HOST`
  - `RABBITMQ_PORT`
  - `RABBITMQ_USER`
  - `RABBITMQ_PASSWORD`
  - `RABBITMQ_VHOST`
  - `EVENT_PUBLISH_RETRIES`
  - `EVENT_PUBLISH_BACKOFF_SECONDS`

#### G0.2 Carpeta de contratos

- Crear una carpeta de contratos de eventos, por ejemplo `events/` o `contracts/events/`.
- Definir el esquema base para cada evento.
- Documentar naming convention de `routing key`.

#### G0.3 Libreria comun

- Crear una capa compartida para:
  - publicar eventos;
  - serializar/deserializar payloads;
  - trazabilidad con `correlation_id`;
  - manejo de `ack/nack`;
  - reintentos y DLQ;
  - logging estructurado.

#### G0.4 Observabilidad

- Agregar trazas de evento en logs JSON.
- Estandarizar `event_id`, `correlation_id` y `source_service` en logs.
- Exponer metricas de:
  - eventos publicados;
  - eventos consumidos;
  - reintentos;
  - eventos muertos en DLQ;
  - latencia de procesamiento.

#### G0.5 Seguridad

- Separar autenticacion de usuario de autenticacion de servicio.
- Para consumo interno, usar credenciales del broker o mTLS si la plataforma lo permite.
- Para auth de usuario, dejar de depender del gRPC de MS-1 en cada request y validar tokens localmente con clave publica/JWKS.

#### G0.6 Criterio de salida

- Un microservicio de prueba publica un evento y otro lo consume desde RabbitMQ.
- El evento sobrevive a reinicio del consumidor.
- Un evento duplicado no genera efectos duplicados.

---

## 3. Estrategia de migracion

### Fase G1 - Inventario de dependencias y corte por prioridad

**Objetivo:** identificar y clasificar todas las dependencias sincrónicas actuales.

#### Actividades

- Catalogar llamadas gRPC entre servicios.
- Marcar las que son estrictamente de consulta y las que son efectos secundarios.
- Mantener temporalmente las consultas inevitables, pero retirar primero notificaciones, reportes y sincronizaciones.
- Definir una matriz `evento -> productor -> consumidores`.

#### Prioridad de migracion

1. Notificaciones.
2. Reportes y estadisticas.
3. Baja/importacion de alumnos y docentes.
4. Calificaciones y cierres de materia.
5. Validacion de auth en request path.

### Fase G2 - Migracion hibrida

**Objetivo:** convivir con RPC y eventos mientras se corta la dependencia directa.

- Los servicios siguen respondiendo por REST/gRPC hacia el cliente.
- Los efectos secundarios pasan al bus.
- Los consumidores van rellenando read models locales.
- Se dejan `feature flags` como `USE_EVENT_BUS=true/false` por servicio.

### Fase G3 - Corte definitivo

**Objetivo:** eliminar gRPC entre servicios en los flujos de negocio que ya tengan cobertura por eventos.

- Retirar llamadas directas a MS-6 desde MS-3 y MS-4.
- Retirar consultas en caliente para reportes si el read model ya es suficiente.
- Retirar validaciones gRPC de auth en runtime si ya existe validacion local de JWT.

---

## 4. Plan por microservicio

---

## 4.1 MS-1 Auth & Users

### Objetivo de migracion

MS-1 debe seguir siendo la autoridad de identidad, pero dejar de ser dependencia sincrona para cada request de los demas MS. Su responsabilidad principal sera emitir tokens, publicar cambios de identidad y proveer llaves publicas para validacion local.

### Dependencias a eliminar

- Evitar que MS-2 a MS-7 llamen a `ValidateToken` por gRPC en cada request.
- Evitar que otros servicios dependan de `GetUserById` para completar flujos normales.

### Fase M1-1 - Publicacion de eventos de identidad

- Publicar `user.created.v1`.
- Publicar `user.updated.v1`.
- Publicar `user.deactivated.v1`.
- Publicar `user.role_changed.v1`.
- Publicar `password.reset_requested.v1` y `password.reset_completed.v1` si el flujo lo requiere.
- Publicar `token.revoked.v1` para invalidacion de refresh tokens o blacklists.

### Fase M1-2 - Validacion local de JWT en otros servicios

- Exponer un mecanismo estable para claves publicas.
- Documentar rotacion de llaves.
- Eliminar la dependencia gRPC de `ValidateToken` en la ruta critica de MS-2 a MS-7.
- Mantener `ValidateToken` solo para casos internos de administracion o compatibilidad transitoria.

### Fase M1-3 - Outbox e idempotencia

- Escribir `outbox` en la misma transaccion que el cambio de usuario.
- Publicar los eventos con un worker separado.
- Registrar `event_id` procesados para evitar reenvio accidental.

### Fase M1-4 - Consumidores internos

- Consumir eventos de cambios de usuario para invalidar cache local si existe.
- Consumir eventos de roles si otros servicios mantienen read models de autorizacion.

### Fase M1-5 - Pruebas y salida

- Pruebas de publicacion con `RabbitMQ` detenido y reanudado.
- Pruebas de duplicados de eventos.
- Pruebas de rotacion de llaves.
- Asegurar que login siga funcionando aunque otros MS esten caidos.

---

## 4.2 MS-2 Periodos & Materias

### Objetivo de migracion

MS-2 debe ser fuente de verdad de periodos y materias, publicar cambios al bus y dejar de depender de servicios remotos para operar su propio CRUD.

### Dependencias a eliminar

- Quitar la validacion gRPC de auth en la ruta critica y reemplazarla por JWT local.
- Evitar que otros servicios consulten MS-2 para datos que pueden persistirse en su propio read model.

### Fase M2-1 - Eventos de dominio

- Publicar `periodo.created.v1`.
- Publicar `periodo.updated.v1`.
- Publicar `periodo.activated.v1`.
- Publicar `periodo.closed.v1`.
- Publicar `materia.created.v1`.
- Publicar `materia.updated.v1`.
- Publicar `materia.assigned_teacher.v1`.
- Publicar `materia.closed.v1`.

### Fase M2-2 - Read models locales

- Mantener una vista local de datos que consumen otros MS si es necesario.
- Permitir que MS-4, MS-6 y MS-7 lean de sus propias proyecciones, no de MS-2 en caliente.

### Fase M2-3 - Outbox y reintentos

- Persistir los eventos de materia/periodo en outbox.
- Reintentar publicaciones fallidas.
- Usar `DLQ` cuando el consumidor falle por datos invalidos.

### Fase M2-4 - Pruebas

- Crear/editar/cerrar materia sin dependencia de otros MS.
- Verificar que el cierre emita un evento y que el sistema siga operativo aunque no exista consumidor.

---

## 4.3 MS-3 Docentes & Alumnos

### Objetivo de migracion

MS-3 suele ser el mayor productor de eventos. Debe importar datos, publicar hechos del dominio y dejar de disparar notificaciones o integraciones directas en el camino principal.

### Dependencias a eliminar

- Eliminar llamadas directas a MS-6 para enviar correos como efecto inmediato.
- Reducir llamadas directas a MS-1 para creacion de usuarios a un flujo asincrono de evento o comando compensado.

### Fase M3-1 - Eventos de importacion y cambios de estado

- Publicar `docente.imported.v1`.
- Publicar `alumno.imported.v1`.
- Publicar `alumno.updated.v1`.
- Publicar `alumno.withdrawn.v1`.
- Publicar `docente.assigned.v1` si aplica.

### Fase M3-2 - Integracion con MS-1 sin acoplar runtime

- Cuando se requiera crear un usuario, usar un flujo asíncrono:
  - MS-3 persiste la intencion local;
  - publica `user.create_requested.v1`;
  - MS-1 consume y crea la cuenta;
  - MS-1 responde con `user.created.v1`.
- En caso de error, dejar registro de estado pendiente y reintento.

### Fase M3-3 - Integracion con MS-6 por eventos

- Reemplazar `SendBienvenida` y `SendBajaNotif` directos por:
  - `alumno.imported.v1` -> MS-6 genera bienvenida;
  - `alumno.withdrawn.v1` -> MS-6 genera baja.

### Fase M3-4 - Read model local

- Mantener datos necesarios para operar sin consultar a otros MS.
- Si un alumno se importa o cambia, actualizar las proyecciones locales.

### Fase M3-5 - Pruebas

- Importacion masiva con broker caido y reanudado.
- Duplicacion de evento de importacion sin duplicar usuario o correo.
- Baja de alumno sin depender de disponibilidad de MS-6.

---

## 4.4 MS-4 Calificaciones

### Objetivo de migracion

MS-4 debe dejar de depender en tiempo real de MS-2 y MS-3 para operar. Debe consumir eventos de materias, alumnos y usuarios y mantener sus propias proyecciones de trabajo.

### Dependencias a eliminar

- Retirar consultas sincrónicas a MS-3 para validar alumnos en la ruta critica.
- Retirar consultas sincrónicas a MS-2 para validar materias o docentes si la informacion puede quedar proyectada localmente.
- Retirar el envio directo de notificaciones a MS-6 desde la logica principal.

### Fase M4-1 - Eventos de calificaciones

- Publicar `actividad.created.v1`.
- Publicar `actividad.updated.v1`.
- Publicar `calificacion.updated.v1`.
- Publicar `concentrado.calculado.v1`.
- Publicar `materia.calificaciones_cerradas.v1`.

### Fase M4-2 - Consumo de eventos upstream

- Consumir `materia.created.v1`, `materia.updated.v1`, `materia.closed.v1` desde MS-2.
- Consumir `alumno.imported.v1`, `alumno.withdrawn.v1` desde MS-3.
- Consumir `user.role_changed.v1` desde MS-1 si afecta permisos.

### Fase M4-3 - Read models locales

- Mantener una tabla o vista proyectada de materias, alumnos y docentes necesarios para calificaciones.
- Basar validaciones del servicio en su propia proyeccion, no en gRPC.

### Fase M4-4 - Notificaciones por evento

- Reemplazar `SendCierreMateria` por un evento `materia.closed.v1`.
- MS-6 consume ese evento y gestiona correos en segundo plano.

### Fase M4-5 - Pruebas

- Calcular, guardar y publicar calificaciones sin contacto con otros MS.
- Cerrar una materia aunque MS-6 no este disponible.
- Reproducir un evento duplicado sin duplicar el efecto.

---

## 4.5 MS-5 Asistencias QR

### Objetivo de migracion

MS-5 debe operar con sus propias sesiones y Redis, usando datos proyectados de alumnos y materias, sin bloquearse por consultas remotas al registrar asistencia.

### Dependencias a eliminar

- Eliminar dependencia gRPC a MS-3 para validacion en cada escaneo.
- Eliminar dependencia sincrona a MS-1 en cada request si el JWT se valida localmente.

### Fase M5-1 - Consumo de eventos de base

- Consumir `alumno.imported.v1`, `alumno.withdrawn.v1`, `materia.created.v1`, `materia.closed.v1`, `periodo.activated.v1`.
- Mantener un read model local para saber si una materia y alumno son elegibles.

### Fase M5-2 - Eventos de asistencia

- Publicar `qr.session.created.v1`.
- Publicar `qr.session.expired.v1`.
- Publicar `asistencia.registered.v1`.
- Publicar `asistencia.rejected.v1`.
- Publicar `session.closed.v1`.

### Fase M5-3 - Redis como cache y anti-replay, no como bus

- Mantener Redis solo para TTL y anti-replay local.
- No usar Redis como reemplazo del bus de eventos.

### Fase M5-4 - Tolerancia a fallos

- Si el bus esta caido, registrar la asistencia localmente en una cola pendiente y publicar cuando el broker vuelva.
- Si una proyeccion esta desactualizada, marcar el caso para reprocesamiento y no bloquear toda la operacion.

### Fase M5-5 - Pruebas

- Registro de asistencia con broker caido y reintento posterior.
- Escaneo duplicado no debe duplicar la asistencia.
- Escaneo cuando la materia ya cerro debe rechazarse con evento de auditoria.

---

## 4.6 MS-6 Notificaciones

### Objetivo de migracion

MS-6 debe convertirse en consumidor principal de eventos de negocio y no en dependencia invocada directamente por otros servicios. Su rol es orquestar el envio de correos desde el bus, con reintentos y auditoria.

### Dependencias a eliminar

- Retirar las invocaciones gRPC directas desde MS-3 y MS-4 como camino principal.
- Evitar que el sistema dependa de disponibilidad de MS-6 para completar transacciones de otros servicios.

### Fase M6-1 - Consumidor de eventos

- Consumir `alumno.imported.v1` -> bienvenida.
- Consumir `alumno.withdrawn.v1` -> baja al docente.
- Consumir `materia.closed.v1` -> cierre a alumnos.
- Consumir `password.reset_requested.v1` -> correo de reseteo.

### Fase M6-2 - Servicio de envio asíncrono

- El envio de correos debe procesarse por workers internos.
- Usar pool de trabajo y `retry` por correo fallido.
- No bloquear el consumo del bus por un correo puntual fallido.

### Fase M6-3 - Auditoria y trazabilidad

- Registrar cada intento en `HistorialCorreo`.
- Guardar `event_id` y `correlation_id` asociados al correo.
- Diferenciar `sent`, `failed`, `retrying`, `dead_letter`.

### Fase M6-4 - Reintentos y DLQ

- Reintentar correos transitoriamente fallidos.
- Enviar a DLQ si el error es permanente.
- Permitir reproceso manual desde DLQ o panel de admin.

### Fase M6-5 - Pruebas

- Matar el broker o el SMTP y comprobar que el resto del sistema sigue funcionando.
- Verificar que el correo puede reintentarse sin duplicar audit logs.
- Validar que el consumo de eventos no se detiene por un mensaje invalido.

---

## 4.7 MS-7 Reportes & Stats

### Objetivo de migracion

MS-7 debe dejar de ser un agregador en caliente que consulta a otros servicios por gRPC cada vez que se pide un reporte. Debe operar sobre proyecciones y snapshots alimentados por eventos.

### Dependencias a eliminar

- Reducir al minimo o eliminar consultas sincrónicas a MS-2, MS-3, MS-4 y MS-5 en la generacion de reportes.
- Eliminar el fallo en cascada cuando un upstream no responde.

### Fase M7-1 - Proyecciones locales

- Consumir eventos de MS-2, MS-3, MS-4 y MS-5.
- Mantener modelos locales para:
  - materias y periodos;
  - alumnos por materia;
  - calificaciones y concentrados;
  - estadisticas de asistencia.

### Fase M7-2 - Generacion de reportes desde snapshot

- Generar Excel y PDF desde la BD/proyeccion local.
- No depender de llamadas gRPC en tiempo real para obtener los datos base.
- Si un evento llega fuera de orden, reordenar por `occurred_at` y version de agregado.

### Fase M7-3 - Cache y reconstruccion

- Mantener cache de reportes si el volumen lo amerita.
- Permitir reconstruir una proyeccion desde el stream de eventos.

### Fase M7-4 - Consistencia eventual

- Documentar que reportes y estadisticas trabajan con consistencia eventual.
- Definir SLA de frescura de datos.
- Si falta un evento, el servicio debe reintentar o marcar el reporte como incompleto, no bloquear todo el sistema.

### Fase M7-5 - Pruebas

- Generar reportes con otros MS caidos.
- Reproducir proyecciones desde cero.
- Validar que los reportes siguen saliendo aunque el broker este temporalmente sin consumidores.

---

## 5. Orden recomendado de implementacion

### Fase 1 - Base de bus y contratos

1. RabbitMQ en `docker-compose`.
2. Contratos de eventos versionados.
3. Libreria comun de publicacion/consumo.
4. Observabilidad y DLQ.

### Fase 2 - Productores principales

1. MS-1 publica eventos de identidad.
2. MS-2 publica periodos y materias.
3. MS-3 publica alumnos y docentes.

### Fase 3 - Consumidores de alto impacto

1. MS-6 consume eventos y envia correos.
2. MS-4 consume eventos para calificaciones.
3. MS-5 consume eventos para asistencia.

### Fase 4 - Desacoplo fuerte

1. MS-7 deja de consultar en caliente.
2. MS-2 a MS-7 validan JWT localmente.
3. Se retiran calls gRPC de efectos secundarios.

### Fase 5 - Hardening

1. Idempotencia completa.
2. Reintentos y backoff.
3. DLQ operativa.
4. Pruebas de caida y recovery.

---

## 6. Criterios de aceptacion globales

El cambio puede considerarse correcto solo si se cumplen todos estos puntos:

- Un microservicio puede caer sin impedir que los demas sigan operando sus funciones basicas.
- Las notificaciones se procesan de forma asíncrona y durable.
- Los reportes no se rompen por la indisponibilidad temporal de otro MS.
- No existen consultas a bases de datos de otros servicios.
- Los consumidores soportan mensajes duplicados sin corromper datos.
- Cada evento tiene trazabilidad completa desde productor hasta consumidor.
- Los flujos criticos no dependen de RPC sincrono entre servicios.

---

## 7. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigacion |
|--------|---------|------------|
| Duplicacion de eventos | Alto | Idempotencia por `event_id` e `inbox` |
| Perdida entre commit y publish | Alto | Patron `outbox` |
| Caida del broker | Alto | Reintento, buffer local temporal, observabilidad |
| Mensajes invalidos | Medio | Validacion de esquema y DLQ |
| Consistencia eventual visible al usuario | Medio | Definir SLA de frescura y mensajes claros |
| Migracion parcial inconsistente | Alto | Feature flags y corte por fases |

---

## 8. Resultado esperado

Al terminar este plan, AGM dejara de comportarse como un monolito distribuido. Cada MS publicara hechos de negocio en el bus, otros servicios reaccionaran a esos eventos de forma asíncrona y la caida de un servicio no detendra el flujo de los demas. gRPC quedara solo para consultas puntuales o compatibilidad temporal, no como eje de acoplamiento del sistema.
