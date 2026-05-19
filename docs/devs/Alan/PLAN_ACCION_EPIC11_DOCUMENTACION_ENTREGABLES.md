# Plan de acción — Documentación y Entregables (Epic 11)

**Responsable principal:** Alane (documentación transversal; el equipo completo aporta contenido y revisiones)  
**Alcance:** `docs/backlog_AGM_completo.md` — **Epic 11 (ISSUE-1101 … ISSUE-1106)**  
**Enunciado:** `docs/Proyecto_Final_SW_AGM.md` — **§6 Entregables**, **§7** criterios de evaluación y penalizaciones, **§4.1** roles en README, **§4.3** GitHub  
**Contexto:** `docs/CONTEXTO_GLOBAL_PROYECTO.md` — arquitectura para diagramas

> Esta épica **no** es código de un microservicio: son **entregables académicos y de calidad** que condicionan la calificación (§6: ausencia de entregables obligatorios impacta evaluación; §7.2 penalizaciones).

---

## 1. Objetivo del plan

Garantizar que, antes de la presentación, existan y estén **completos, coherentes con el sistema desplegado** y **listos para el docente**:

1. **README** del repositorio (instalación, roles, URLs, video).  
2. **Manual de usuario** (PDF/Word profesional).  
3. **Manual técnico** (arquitectura, datos, gRPC, APIs, despliegue).  
4. **Postman / OpenAPI** exportados en el repo.  
5. **Video** 10–20 min en YouTube con todos los flujos.  
6. **Checklist** ISSUE-1106 sin ítems pendientes.

---

## 2. Mapa de issues y dependencias

| Issue | Entregable | Depende de (típico) |
|-------|------------|---------------------|
| 1101 | README | MS desplegados, Compose estable (Epic 1) |
| 1102 | Manual usuario | Sistema en prod + capturas reales |
| 1103 | Manual técnico | Diagramas, protos, modelo datos (todos los MS) |
| 1104 | Postman/OpenAPI | Endpoints estables en los 7 MS |
| 1105 | Video | Mismo que manual + correos reales |
| 1106 | Checklist QA | Todo lo anterior + reglas de negocio verificadas |

**Orden recomendado:** 1101 (esqueleto temprano) → 1104 (iterativo) → 1103/1102 (en paralelo tras estabilizar) → 1105 → 1106 cierre.

---

## 3. ISSUE-1101 — README principal

### Tareas detalladas

| # | Contenido obligatorio (§6.4 + backlog) | Verificación |
|---|----------------------------------------|----------------|
| 1101.1 | Descripción 1–2 párrafos AGM | Lectura clara en < 1 min |
| 1101.2 | Tabla integrantes **nombre + rol** (líder, dev MS-X, DBA, DevOps, QA) | Cumple §4.1 |
| 1101.3 | Tabla **MS → stack → BD** | 7 filas |
| 1101.4 | Prerrequisitos (Docker, Compose, versiones) | Versiones numéricas |
| 1101.5 | Pasos: clonar → `.env.example` → `.env` por MS → `docker compose up --build` | Probar en máquina limpia (1106) |
| 1101.6 | Tabla **URLs HTTPS producción** por MS | Enlaces clicables |
| 1101.7 | URL **video YouTube** | |
| 1101.8 | Estructura carpetas (`/ms-*`, `/proto`, `/frontend`) | Diagrama o lista |

### Errores a evitar

- URLs localhost como “producción”.  
- Contraseñas o tokens en el README.  
- README desactualizado respecto al gateway (rutas `/auth/*`, etc.).

---

## 4. ISSUE-1102 — Manual de usuario

### Estructura mínima (backlog + §6.1)

1. Portada (proyecto, equipo, materia, fecha).  
2. Índice con **hipervínculos**.  
3. Introducción y propósito.  
4. **Acceso:** URL frontend o Swagger/Postman + cómo obtener token.  
5. **Administrador:** periodos, import PDF materias, import PDF docentes, gestión docentes (capturas **producción**).  
6. **Docente:** ponderaciones, import alumnos, calificaciones, QR, export reporte.  
7. **Alumno:** calificaciones, QR, baja.  
8. Numeración, encabezados/pies, estilo consistente.

### Calidad “a prueba de errores”

| Control | Acción |
|---------|--------|
| Capturas | Fecha visible o versión app; mismo tema claro/oscurro unificado |
| Datos sensibles | Difuminar correos/matriculas si política BUAP lo exige |
| Pasos | Numerados; un paso = una acción |
| Glosario | NRC, periodo activo, baja irreversible |

---

## 5. ISSUE-1103 — Manual técnico

### Contenidos obligatorios (backlog)

| Sección | Qué documentar |
|---------|----------------|
| Arquitectura | Diagrama: cliente → Nginx → 7 MS; puertos REST **8001–8007** y gRPC **50051–50057**; 7 MySQL + Redis MS-5 |
| Stack | Justificación breve por MS (puede referenciar `Proyecto_Final` §5.4.4) |
| Datos | ER o esquema + **diccionario de datos** por `agm_*_db` |
| gRPC | Cada `.proto`: servicios, mensajes, quién llama a quién (`CONTEXTO_GLOBAL` §5) |
| REST | Por MS: método, path, query, body, respuestas, códigos error |
| Instalación local | Paso a paso (puede remitir al README si está duplicado) |
| Despliegue prod | Railway/Render/Fly: variables, HTTPS, orden de despliegue |

### Herramientas sugeridas

- Diagramas: draw.io, Lucidchart, **Mermaid** en Markdown exportable a PDF.  
- Tablas de endpoints: generadas desde OpenAPI si usan `drf-spectacular`.

---

## 6. ISSUE-1104 — Postman / OpenAPI

| # | Tarea | Criterio |
|---|--------|----------|
| 1104.1 | Colección con **7 carpetas** (una por MS) | |
| 1104.2 | Variables `{{base_url_gateway}}`, `{{access_token}}` | |
| 1104.3 | Request de login guarda token en variable | Flujo reutilizable |
| 1104.4 | Ejemplos body/response por endpoint crítico | |
| 1104.5 | Export `postman_collection.json` en repo (ruta acordada, ej. `/docs/postman/`) | |
| 1104.6 | Alternativa: `openapi.yaml` por MS o agregado | |

**Revisión:** un compañero importa colección en Postman nuevo y ejecuta flujo admin sin ayuda.

---

## 7. ISSUE-1105 — Video demostrativo

### Restricciones duras (§6.3 + backlog)

- Duración **10–20 minutos**.  
- YouTube (puede ser **no listado** con enlace).  
- Contenido mínimo por bloques de tiempo (backlog 1105):

| Min aprox | Contenido |
|-----------|-------------|
| 0–2 | Equipo, nombres, roles |
| 2–4 | GitHub, URLs prod, estructura repo |
| 4–7 | **Admin:** login, periodo, import PDF materias, import PDF docentes |
| 7–12 | **Docente:** import alumnos, ponderaciones, calificaciones, QR, cerrar materia, export |
| 12–15 | **Alumno:** login clave única, calificaciones, QR, baja |
| 15–17 | **Correos reales** (bandeja o captura entrega) |
| 17–20 | Frontend móvil **si** existe punto extra |

### Producción técnica

- Audio claro; resolución mínima 1080p recomendado.  
- Mostrar **navegador** y/o Postman con URLs **HTTPS** reales.  
- Evitar edición que oculte errores: si algo falla en grabación, re-grabar tramo.

---

## 8. ISSUE-1106 — Checklist pre-entrega

Usar como **tabla de cierre** (copiar a issue tracker o `docs/CHECKLIST_PREENTREGA.md`):

- [ ] 7 MS HTTPS públicos.  
- [ ] `docker compose up --build` en máquina limpia.  
- [ ] **>20 commits** y actividad repartida (§7.2).  
- [ ] Sin credenciales en código (`git grep -i password`, `api_key`, `secret`).  
- [ ] Todos los `.env.example` presentes.  
- [ ] `/proto` completo y compilable.  
- [ ] ≥3 pares gRPC funcionando.  
- [ ] Ponderaciones ≠100% rechazadas.  
- [ ] Anti-replay QR.  
- [ ] Redondeo 7.5→8, 7.4→7.  
- [ ] Baja irreversible + notificación docente.  
- [ ] Manuales + video listos.  
- [ ] Postman en repo.

---

## 9. Roles sugeridos en el equipo (RACI liviano)

| Actividad | Responsable | Apoyo |
|-----------|-------------|--------|
| README vivo | Alane | DevOps (URLs) |
| Manuales redacción | Alane | Todos (capturas por rol) |
| Diagrama arquitectura | Alane | Quien diseñó Compose |
| Postman | Alane | Un dev por MS verifica carpeta |
| Video guion + grabación | Líder o rotación | Todos en escena §6.3 |
| Checklist final | Alane + líder | Equipo completo |

---

## 10. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Manuales con capturas de localhost | Re-capturar en prod antes de entregar |
| Video desactualizado | Grabar **después** del freeze de features |
| OpenAPI desincronizado | Generar desde código o revisión por MS antes de entrega |
| Penalización commits (§7.2) | Commits pequeños y frecuentes durante el semestre |

---

## 11. Checklist salida Epic 11

- [ ] ISSUE-1101 … 1106 todos marcados.  
- [ ] Enlaces en README: prod + video.  
- [ ] Manuales en PDF (o Word) en repo o Drive con enlace estable documentado.  
- [ ] Evaluación §7 “Documentación técnica” y “Calidad repositorio” cubiertas explícitamente.  

---

## 12. Referencias

- `docs/backlog_AGM_completo.md` — Epic 11  
- `docs/Proyecto_Final_SW_AGM.md` — §6, §7, §4.1, §4.3  
- `docs/CONTEXTO_GLOBAL_PROYECTO.md`  
- `docs/Proyecto_Final_SW_AGM.md` §6.3 guion video  
