# Plan de acción — MS-5 Asistencias QR (Epic 7)

**Desarrollador:** Guillermo  
**Microservicio:** MS-5 — Asistencias QR  
**Carpeta:** `/ms-asistencias/`  
**REST:** `8005` · **gRPC:** `50055` · **BD:** MySQL `agm_asistencias_db` + **Redis** (obligatorio en este MS)  
**Backlog:** `docs/backlog_AGM_completo.md` — **Epic 7 (ISSUE-701 … ISSUE-708)**  
**Enunciado:** `docs/Proyecto_Final_SW_AGM.md` — §5.2.2 pase de lista QR, §5.3 Módulo 6, §5.4.1 tabla MS-5  
**Contexto:** `docs/CONTEXTO_GLOBAL_PROYECTO.md` — §4 (Redis solo MS-5), §5  
**Especificación:** `docs/microservicios/MS5_ASISTENCIAS_QR.md`  
**Contrato:** `proto/asistencias.proto`

---

## 1. Rol del MS-5

MS-5 implementa el **módulo de asistencia por QR dinámico**:

- Sesiones de **10 minutos** por materia.  
- QR con **cifrado/HMAC** y **ventana corta de validez** (~30 s) para anti-fraude.  
- Clasificación **Presente** (primeros 5 min de la sesión) vs **Retardo** (minuto 5–10).  
- **Anti-replay:** un mismo payload no registra dos asistencias.  
- Estadísticas para docente (incl. tiempo real durante la sesión) y datos vía **gRPC** para MS-7.

**No hace:** gestión de periodos, lista de alumnos maestra (eso es MS-3); valida inscripción vía gRPC.

---

## 2. Contrato gRPC (`asistencias.proto`)

| RPC | Entrada | Salida | Consumidor típico |
|-----|---------|--------|-------------------|
| `GetAsistenciaAlumno` | `alumno_id`, `materia_id` | `AsistenciaAlumnoResponse` (totales, `repeated RegistroAsistencia`) | MS-7 estadísticas alumno |
| `GetEstadisticasAsistencia` | `materia_id` | `EstadisticasAsistenciaResponse` (grupal + `repeated AsistenciaAlumnoResumen`) | MS-7 reportes |

**Nota:** el proto incluye `matricula` y `nombre` en resúmenes; si MS-5 no debe duplicar datos sensibles, puede rellenar solo IDs y dejar enriquecimiento a MS-7 — **debe coincidir** con lo implementado y con los tests.

---

## 3. Clientes gRPC salientes (MS-5 → otros)

| Destino | Métodos | Uso |
|---------|---------|-----|
| MS-1 | `ValidateToken` | Proteger todo REST |
| MS-3 | `GetAlumnoById`, `IsAlumnoEnMateria` | Validar alumno al generar QR y al registrar |

---

## 4. Redis — claves y TTL (diseño robusto)

| Clave / patrón | Propósito | TTL sugerido |
|----------------|-----------|--------------|
| `sesion:{sesion_id}` | Estado de sesión activa (materia, inicio epoch, docente) | **600 s** (10 min) alineado a ISSUE-702 |
| `qr_used:{hash_payload}` | Anti-replay tras escaneo exitoso | Backlog **ISSUE-704** sugiere `EX 60`; MS5 doc menciona 600 — **usar ventana corta (60–120 s)** suficiente para evitar doble escaneo del mismo token; documentar valor en `.env.example` |

**Regla:** solo **una sesión activa por `materia_id`** (constraint en MySQL + comprobación en Redis antes de crear).

---

## 5. Plan por issue

### ISSUE-701 — Configuración base Django (MS-5)

| # | Tarea | Criterio |
|---|--------|----------|
| 701.1 | Proyecto en `/ms-asistencias/`, Django 5 + DRF | `migrate` OK |
| 701.2 | MySQL `agm_asistencias_db`, `utf8mb4` | Conexión estable |
| 701.3 | Redis (`django-redis` o `redis` nativo) | Ping en healthcheck |
| 701.4 | Modelos `SesionAsistencia`, `RegistroAsistencia` | `unique_together` sesión+alumno |
| 701.5 | `cryptography` / HMAC secret desde env `QR_SECRET_KEY` o similar | Nunca en código fuente |
| 701.6 | Stubs gRPC MS-1 y MS-3 | Generados desde `/proto` |

**Fallos típicos:** Redis no levantado en Compose; MS-5 arranca pero todas las sesiones fallan.

---

### ISSUE-702 — Gestión de sesiones

| # | Tarea | Criterio |
|---|--------|----------|
| 702.1 | `POST /sesiones/iniciar` con `materia_id` | Docente validado como titular (gRPC MS-2 si el patrón del repo valida docente por materia) |
| 702.2 | Persistir sesión en MySQL; `fin = inicio + 10 min` | Recuperable tras caída de Redis |
| 702.3 | Publicar estado en Redis con TTL 600 | Expira solo al terminar ventana |
| 702.4 | Rechazar segunda sesión activa misma materia | 409 Conflict o 400 con mensaje claro |
| 702.5 | `DELETE /sesiones/:id/cerrar` | `activa=False` en MySQL + limpiar claves Redis asociadas |
| 702.6 | Cierre automático al expirar TTL | Worker periódico, Celery beat, o señal al leer sesión: marcar inactiva en MySQL |
| 702.7 | `GET /sesiones/:materiaId/activa` | 404 si no hay sesión activa |

---

### ISSUE-703 — Generación de token / payload QR

| # | Tarea | Criterio |
|---|--------|----------|
| 703.1 | `GET /qr/generate` (o `?materia_id=`) | Solo rol alumno; `IsAlumnoEnMateria` true |
| 703.2 | Incluir en el payload: `alumno_id`, `sesion_id` (sesión activa de esa materia), `timestamp` | Si no hay sesión activa → 404 o mensaje “no hay pase de lista” |
| 703.3 | Firma HMAC (SHA256 recomendado) sobre concatenación acordada | Verificación simétrica en 704 |
| 703.4 | Validez **30 s** | Respuesta incluye `expires_in` |
| 703.5 | Rotación | Segunda petición antes de expirar genera nuevo timestamp/firma |

**Seguridad:** no incluir datos personales innecesarios en claro si el payload fuera leído; el HMAC ya limita falsificación.

---

### ISSUE-704 — Registro de asistencia (`POST /asistencias/registrar`)

| # | Tarea | Criterio |
|---|--------|----------|
| 704.1 | Parsear `qr_payload` del body | Formato estricto |
| 704.2 | Verificar HMAC | 400 si inválido |
| 704.3 | Verificar `timestamp` + ventana 30 s | 400 si expirado |
| 704.4 | `SET qr_used:{hash} 1 NX EX <ventana>` | Si `NX` falla → ya usado → 400 |
| 704.5 | Sesión activa en Redis para la **misma** materia que la del token | Coherencia sesión_id |
| 704.6 | Calcular minutos desde `inicio` de sesión (servidor) | ≤5: `presente`; >5 y ≤10: `retardo`; fuera de ventana: 400 |
| 704.7 | Insertar `RegistroAsistencia` | Idempotencia por `unique_together` |
| 704.8 | Actualizar contadores Redis para ISSUE-706 | Opcional en misma transacción lógica |

---

### ISSUE-705 — Consultas

| # | Tarea | Criterio |
|---|--------|----------|
| 705.1 | `GET /asistencias/:materiaId/hoy` | Filtra por fecha local del servidor o TZ configurada |
| 705.2 | `GET /asistencias/:materiaId/historial` | `page`, `limit`, filtro `fecha` (enunciado §5.4.5 paginación) |
| 705.3 | `GET /asistencias/alumno/:alumnoId/materia/:materiaId` | Alumno solo su propio id; docente/admin según reglas |

---

### ISSUE-706 — Estadísticas en tiempo real

| # | Tarea | Criterio |
|---|--------|----------|
| 706.1 | `GET /sesiones/:id/stats` | `total_alumnos` (desde MS-3 o valor cacheado al inicio), `presentes`, `retardos`, `ausentes` |
| 706.2 | Actualización en Redis al cada registro exitoso | Latencia baja para UI docente |

**Definición de “ausente”:** alumnos inscritos − (presentes + retardos) **solo para esa sesión** si el equipo cuenta lista cerrada; documentar.

---

### ISSUE-707 — Servidor gRPC

| # | Tarea | Criterio |
|---|--------|----------|
| 707.1 | Implementar `GetAsistenciaAlumno` y `GetEstadisticasAsistencia` | Paridad con `asistencias.proto` |
| 707.2 | Puerto **50055** | Sin conflicto |
| 707.3 | Datos consistentes con MySQL | No solo Redis |

---

### ISSUE-708 — Confirmar / solicitar nueva lista

| # | Tarea | Criterio |
|---|--------|----------|
| 708.1 | `POST /sesiones/:id/confirmar` | Cierra sesión, congela registros, opcional estado “confirmada” |
| 708.2 | `POST /sesiones/:id/solicitar-nueva` | Invalida sesión actual, borra Redis, permite nuevo `iniciar` (definir si borra registros MySQL o solo abre nueva sesión — **alinear con negocio**; enunciado: repetir pase ante irregularidad) |

---

## 6. Autorización (resumen)

| Endpoint | Admin | Docente | Alumno |
|----------|-------|---------|--------|
| Iniciar/cerrar sesión, registrar QR, stats sesión | Según política | Titular de la materia | No |
| Generar QR | No | No | Inscrito en la materia |
| Historial materia | Sí | Titular | No (o solo su fila vía otro endpoint) |

---

## 7. Matriz de pruebas obligatorias

| ID | Caso | Esperado |
|----|------|----------|
| A1 | Iniciar sesión | Redis TTL 600, MySQL `activa=True` |
| A2 | Iniciar duplicado misma materia | Error controlado |
| A3 | QR válido minuto 3 | `presente` |
| A4 | QR válido minuto 7 | `retardo` |
| A5 | Mismo QR dos veces | Segundo rechazado (anti-replay) |
| A6 | QR con firma incorrecta | 400 |
| A7 | Sesión expirada | 400 al registrar |
| A8 | gRPC `GetEstadisticasAsistencia` | Respuesta con lista de alumnos coherente con MS-3 |

---

## 8. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Desfase de reloj contenedor | NTP / usar siempre hora del servidor para ventanas |
| Redis volátil pierde sesión | MySQL como fuente de verdad para reconstruir estado mínimo |
| Docente escanea QR de otra materia | Validar `materia_id` implícita en sesión vs token |
| Carga concurrente | Transacciones DB + `select_for_update` si hay carreras en “primera asistencia” |

---

## 9. Checklist de salida Epic 7

- [ ] ISSUE-701 … 708 completados.  
- [ ] Demo enunciado: sesión 10 min, presente/retardo, cierre automático.  
- [ ] Anti-replay demostrable (ISSUE-1106 checklist proyecto).  
- [ ] Postman/colección con flujo docente + alumno.  
- [ ] Variables Redis y `QR_SECRET` en `.env.example`.  

---

## 10. Referencias

- `docs/backlog_AGM_completo.md` — Epic 7  
- `docs/Proyecto_Final_SW_AGM.md` — Módulo 6 Asistencias QR  
- `docs/microservicios/MS5_ASISTENCIAS_QR.md`  
- `proto/asistencias.proto`  
