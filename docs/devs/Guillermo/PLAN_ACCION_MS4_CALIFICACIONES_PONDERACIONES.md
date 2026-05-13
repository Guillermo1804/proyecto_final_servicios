# Plan de acción — MS-4 Calificaciones y Ponderaciones (Epic 6)

**Desarrollador:** Guillermo  
**Microservicio:** MS-4 — Calificaciones & Ponderaciones  
**Carpeta:** `/ms-calificaciones/`  
**REST:** `8004` · **gRPC:** `50054` · **BD:** MySQL `agm_calificaciones_db`  
**Backlog:** `docs/backlog_AGM_completo.md` — **Epic 6 (ISSUE-601 … ISSUE-609)**  
**Enunciado:** `docs/Proyecto_Final_SW_AGM.md` — §5.2.2 (ponderaciones, actividades, concentrado, cierre, export vía MS-7), §5.3 Módulos 4 y 5, §5.4.1 MS-4  
**Contexto:** `docs/CONTEXTO_GLOBAL_PROYECTO.md` — §5 (MS-4 llama MS-1,2,3,6)  
**Especificación:** `docs/microservicios/MS4_CALIFICACIONES.md`  
**Contrato:** `proto/calificaciones.proto`

---

## 1. Rol del MS-4

MS-4 es la **fuente de verdad** de:

- **Ponderaciones** por materia (categorías que suman **exactamente 100%**).  
- **Actividades** (entregas evaluables) por categoría.  
- **Calificaciones** por actividad y alumno (manual o Excel).  
- **Promedio ponderado real** y **redondeo institucional** (fracción ≥ 0.5 → entero superior).  
- **Concentrado** por materia (vista docente/admin).  
- **Estado de cierre** de materia: cerrada + **lista impresa** bloquea ediciones.  
- **gRPC** para MS-7 y cualquier consumidor interno.

**No hace:** enviar correos (MS-6); listar alumnos maestros (MS-3); definir periodos (MS-2).

---

## 2. Contrato gRPC (`calificaciones.proto`)

| RPC | Uso |
|-----|-----|
| `GetConcentrado(materia_id)` | Tabla por alumno: actividades, `promedio_real`, `promedio_redondeado`; estructura jerárquica con `CategoriaConcentrado` |
| `GetPromedioAlumno(alumno_id, materia_id)` | `PromedioResponse` |
| `GetEstadisticasMateria(materia_id)` | Totales, aprobados/reprobados (proto: redondeado ≥ 6 aprueba — **validar** contra reglamento BUAP del curso) |

**Consistencia REST ↔ gRPC:** el mismo motor de cálculo debe alimentar `GET /concentrado` y `GetConcentrado` (servicio interno único).

---

## 3. Clientes gRPC salientes

| Destino | Métodos | Cuándo |
|---------|---------|--------|
| MS-1 | `ValidateToken`, opcional `CheckRole` | Cada request REST |
| MS-2 | `GetMateriaById` | Verificar docente titular de la materia en ponderaciones/actividades/calificaciones |
| MS-3 | `IsAlumnoEnMateria`, `GetAlumnosByMateria` | Validar calificación; armar concentrado con nombres |
| MS-6 | `SendCierreMateria` | Tras `POST .../cerrar` |

---

## 4. Modelo de datos (resumen)

| Modelo | Campos clave | Reglas |
|--------|----------------|--------|
| `Ponderacion` | `materia_id`, `nombre_categoria`, `porcentaje` | Suma por `materia_id` = **100.00** |
| `Actividad` | FK `ponderacion`, `nombre`, `fecha` | Borrar solo si no hay `Calificacion` |
| `Calificacion` | `actividad`, `alumno_id`, `calificacion` 0–10, 2 decimales | `unique_together` (actividad, alumno_id) |
| `EstadoMateria` | `materia_id` único, `cerrada`, `lista_impresa` | Si `lista_impresa`: bloquear PUT calificaciones |

---

## 5. Motor de cálculo (crítico — ISSUE-606)

### 5.1 Promedio ponderado

Por cada categoría de ponderación \(c\) con porcentaje \(p_c\) (%):

1. Promedio de calificaciones del alumno en actividades de esa categoría: \(\bar{g}_c\) (si no hay notas, acordar: 0 o excluir categoría — **documentar**; el doc MS4 sugiere 0).  
2. Contribución: \(\bar{g}_c \times (p_c / 100)\).  
3. **Promedio real** = suma de contribuciones.

### 5.2 Redondeo institucional

- Parte decimal \(d = \text{promedio\_real} - \lfloor \text{promedio\_real} \rfloor\) (manejar negativos si no aplica en 0–10).  
- Si \(d \geq 0.5\) → `promedio_redondeado = ceil(real)`  
- Si \(d < 0.5\) → `promedio_redondeado = floor(real)`  

**Casos de prueba obligatorios:** `7.5 → 8`, `7.4 → 7`, `6.0 → 6`, límite `10.0`, borde `X.499999` vs `X.5` con Decimal en Python.

Usar `Decimal` en negocio para evitar errores de float IEEE.

---

## 6. Plan por issue

### ISSUE-601 — Configuración base

| # | Tarea | Criterio |
|---|--------|----------|
| 601.1 | Django 5 + DRF en `/ms-calificaciones/` | `check` OK |
| 601.2 | MySQL `agm_calificaciones_db` | Migraciones |
| 601.3 | Modelos Ponderación, Actividad, Calificacion | Admin opcional para debug |
| 601.4 | `openpyxl` para importaciones | En requirements |

---

### ISSUE-602 — Ponderaciones

| # | Tarea | Criterio |
|---|--------|----------|
| 602.1 | `GET/POST/PUT /ponderaciones/:materiaId` | JSON con lista de categorías |
| 602.2 | Validación **suma = 100%** | 400 con detalle de suma actual |
| 602.3 | Autorización | Solo docente de la materia (MS-2) o admin |
| 602.4 | `POST .../importar` Excel | Misma validación de suma tras parseo |

---

### ISSUE-603 — Actividades

| # | Tarea | Criterio |
|---|--------|----------|
| 603.1 | `POST /actividades` | FK a ponderación existente de la misma materia |
| 603.2 | `GET /actividades?materia=:id` | Agrupado por categoría |
| 603.3 | `PUT` / `DELETE` | DELETE bloqueado si hay calificaciones |

---

### ISSUE-604 — Calificaciones individuales

| # | Tarea | Criterio |
|---|--------|----------|
| 604.1 | `POST /calificaciones` | Body: actividad_id, alumno_id, calificación |
| 604.2 | `IsAlumnoEnMateria` | 400 si alumno no inscrito activo |
| 604.3 | Rango 0–10, dos decimales | Validación DRF/serializer |
| 604.4 | `PUT /calificaciones/:id` | Bloqueado si `lista_impresa` |
| 604.5 | Upsert | Definir si POST actualiza o solo crea (unique constraint) |

---

### ISSUE-605 — Importación Excel

| # | Tarea | Criterio |
|---|--------|----------|
| 605.1 | Columnas: matrícula, actividad_id, calificación | Mapeo documentado |
| 605.2 | Resolver `alumno_id` vía MS-3 por matrícula o importar solo ids | Sin asumir BD compartida |
| 605.3 | Respuesta con resumen éxitos/fallos | Fila a fila motivo |

---

### ISSUE-606 — Cálculo (servicio compartido)

| # | Tarea | Criterio |
|---|--------|----------|
| 606.1 | Función pura `calcular_promedio_ponderado(alumno_id, materia_id)` | Unit tests |
| 606.2 | Función `redondear_institucional(real)` | Unit tests tabla de bordes |
| 606.3 | Invalidación | Cualquier cambio en `Calificacion` refleja en próximo GET |

---

### ISSUE-607 — Concentrado REST

| # | Tarea | Criterio |
|---|--------|----------|
| 607.1 | `GET /concentrado/:materiaId` | Lista alumnos con gRPC MS-3 |
| 607.2 | Columnas por actividad | Orden estable |
| 607.3 | Incluir promedio real y redondeado | Coincide con gRPC |
| 607.4 | Paginación si lista muy larga | Alineado §5.4.5 |

---

### ISSUE-608 — Cierre de materia

| # | Tarea | Criterio |
|---|--------|----------|
| 608.1 | Modelo `EstadoMateria` | Crear al primer uso o migración inicial |
| 608.2 | `POST /materias/:id/cerrar` | `cerrada=True`; gRPC `SendCierreMateria` |
| 608.3 | `POST /materias/:id/imprimir-lista` | `lista_impresa=True` |
| 608.4 | Bloqueo | `PUT` calificaciones → 403 si lista impresa |
| 608.5 | Orden enunciado | Cierre puede ocurrir antes de imprimir; bloqueo duro solo tras imprimir |

**Manejo de fallo MS-6:** si `SendCierreMateria` falla, decidir transacción: rollback de `cerrada` o estado “cierre_pendiente_notif” — **documentar** para no dejar materia “cerrada” sin correo sin avisar.

---

### ISSUE-609 — Servidor gRPC

| # | Tarea | Criterio |
|---|--------|----------|
| 609.1 | Implementar los 3 RPC según `calificaciones.proto` | Incluir `repeated CategoriaConcentrado` y actividades en concentrado |
| 609.2 | Puerto **50054** | |
| 609.3 | Errores | `NOT_FOUND` si materia sin datos locales; validar permisos si el RPC no lleva JWT (según diseño: metadata o confianza red interna) |

---

## 7. Formato JSON estándar

Respuestas REST (no binarias): `{ "success": true, "data": {...}, "message": "" }` según `CONTEXTO_GLOBAL_PROYECTO.md` §6.1.

---

## 8. Matriz de pruebas

| ID | Caso | Esperado |
|----|------|------------|
| C1 | Ponderaciones 40+30+20+10 | 200 |
| C2 | Ponderaciones 40+30+20+9 | 400 |
| C3 | Calificación alumno no inscrito | 400 |
| C4 | Promedio 7.5 | redondeado 8 |
| C5 | Lista impresa | PUT calificación 403 |
| C6 | Cerrar materia | MS-6 invocado (mock o integración) |
| C7 | `GetConcentrado` vs REST | Mismos números |

---

## 9. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Float en calificaciones | `Decimal` en modelo y cálculo |
| Docente no autorizado modifica otra materia | Siempre validar titular vía MS-2 |
| Performance concentrado grande | Consultas optimizadas, `select_related`, índices en FKs |
| Desincronía proto | Regenerar stubs en cada PR que toque `/proto` |

---

## 10. Checklist de salida Epic 6

- [ ] ISSUE-601 … 609 completados.  
- [ ] Regla de redondeo verificada (checklist ISSUE-1106 proyecto).  
- [ ] Integración MS-3 y MS-2 probada en flujo real.  
- [ ] `SendCierreMateria` probado (o mockeado con evidencia).  
- [ ] Postman: ponderaciones → actividades → calificaciones → concentrado → cerrar → imprimir lista.  

---

## 11. Referencias

- `docs/backlog_AGM_completo.md` — Epic 6  
- `docs/Proyecto_Final_SW_AGM.md` — §5.2.2, §5.3 módulos 4–5  
- `docs/microservicios/MS4_CALIFICACIONES.md`  
- `proto/calificaciones.proto`  
