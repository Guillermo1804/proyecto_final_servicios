# Plan de acción — MS-3 Docentes & Alumnos (Epic 5)

**Desarrollador:** Alane  
**Microservicio:** MS-3 — Docentes & Alumnos  
**Carpeta:** `/ms-alumnos/`  
**REST:** `8003` · **gRPC:** `50053` · **BD:** MySQL `agm_alumnos_db`  
**Backlog:** `docs/backlog_AGM_completo.md` — **Epic 5 (ISSUE-501 … ISSUE-509)**  
**Enunciado:** `docs/Proyecto_Final_SW_AGM.md` — §5.2.1 (import docentes, catálogo), §5.2.2 (import alumnos, baja), §5.2.3 (dashboard alumno), §5.3 Módulos 3–4, §5.4.1 MS-3  
**Contexto:** `docs/CONTEXTO_GLOBAL_PROYECTO.md` — §4 (seeds BUAP), §5  
**Especificación:** `docs/microservicios/MS3_DOCENTES_ALUMNOS.md`  
**Contrato:** `proto/alumnos.proto`

---

## 1. Rol del MS-3

MS-3 es el **directorio académico operativo**:

- **Docentes:** importación PDF institucional, CRUD, reset password vía MS-1.  
- **Alumnos:** entidad + **inscripción por materia** (`materia_id` lógico a MS-2), import Excel/CSV con **vista previa**, creación de usuario en MS-1 y correo bienvenida (MS-6).  
- **Baja de materia:** irreversible, notificación al docente (MS-6).  
- **gRPC** para MS-4, MS-5, MS-6, MS-7 y validaciones cruzadas con MS-2.

**Modelo recomendado:** `Docente`, `Alumno`, `InscripcionMateria` (con `activo`, `baja_solicitada`, `fecha_baja`) como en `MS3_DOCENTES_ALUMNOS.md` — más robusto que meter `materia_id` solo en `Alumno` si el alumno cursa varias materias.

---

## 2. Resultados medibles

| # | Resultado | Evidencia |
|---|------------|-----------|
| D1 | Migraciones + seeds opcionales | `test-data/seed_*.sql` cargables según doc |
| D2 | Import PDF docentes | Usuarios en MS-1 + filas `Docente` |
| D3 | Import Excel alumnos | Preview + confirmación; `SendBienvenida` |
| D4 | Baja alumno | `IsAlumnoEnMateria` false; correo docente |
| D5 | gRPC `AlumnosService` | RPC del proto + `GetDocenteByUsuarioId` |
| D6 | Docente solo su materia | gRPC `GetMateriaById` MS-2 para validar titularidad |

---

## 3. Contrato gRPC (`alumnos.proto`)

| RPC | Uso |
|-----|-----|
| `GetAlumnosByMateria` | Lista inscritos **activos** (excluye bajas) |
| `GetAlumnoById` | Datos para correos MS-6, QR MS-5 |
| `IsAlumnoEnMateria` | MS-4 calificaciones, MS-5 QR |
| `GetDocenteByUsuarioId` | MS-6 notificación baja (resolver email docente) |

**Extensión futura:** si MS-2 necesita enlazar docente por nombre desde PDF, valorar `GetDocenteByNombre` o búsqueda fuzzy — coordinar con Alane (MS-2) y Epic 2.

---

## 4. Clientes gRPC salientes

| MS | Métodos | Uso |
|----|---------|-----|
| MS-1 | `ValidateToken`, `CreateUser` | Auth; alta usuarios import |
| MS-2 | `GetMateriaById` | Validar docente de materia; `me/materias` enriquecido |
| MS-6 | `SendBienvenida`, `SendBajaNotif` | Correos transaccionales |

**`CreateUser`:** password temporal UUID; mismo flujo que REST interno si existe duplicidad.

---

## 5. Plan por issue

### ISSUE-501 — Base Django MS-3

| # | Tarea | Criterio |
|---|--------|----------|
| 501.1 | Proyecto `/ms-alumnos/`, Django 5 + DRF | |
| 501.2 | `openpyxl`, `pandas`, `pdfplumber`, grpcio | |
| 501.3 | Modelos `Docente`, `Alumno`, `InscripcionMateria` | Unique constraints según spec |
| 501.4 | `usuario_id` único por docente/alumno | Alineado MS-1 |
| 501.5 | Seeds BUAP opcionales | Documentar en README |

---

### ISSUE-502 — Import PDF docentes

| # | Tarea | Criterio |
|---|--------|----------|
| 502.1 | `POST /docentes/importar` multipart | Admin |
| 502.2 | Parse nombre, email, cubículo | Tolerante a filas malas |
| 502.3 | Por fila: `CreateUser` MS-1 rol docente + password temp | Idempotencia por email |
| 502.4 | Persistir `Docente` con `usuario_id` | |
| 502.5 | MS-6 correo bienvenida docente | Si el flujo lo incluye (spec MS3) |
| 502.6 | Duplicado email | Actualizar datos locales + usuario existente sin duplicar |

---

### ISSUE-503 — CRUD docentes

| # | Tarea | Criterio |
|---|--------|----------|
| 503.1 | `GET /docentes` | Paginación + búsqueda admin |
| 503.2 | `GET /docentes/:id` | Admin o self |
| 503.3 | `PUT /docentes/:id` | Admin |
| 503.4 | `POST /docentes/:id/reset-password` | Llamada MS-1 (HTTP interno o política del repo) |

---

### ISSUE-504 — Import alumnos Excel/CSV

| # | Tarea | Criterio |
|---|--------|----------|
| 504.1 | `POST .../importar/:materiaId?preview=true` | No persiste; devuelve filas parseadas |
| 504.2 | Confirmación sin `preview` | Transacción por lote razonable |
| 504.3 | Crear `Alumno` + `InscripcionMateria` | O reutilizar alumno existente por matrícula |
| 504.4 | `CreateUser` alumno + `SendBienvenida` con clave | gRPC MS-6 con `clave_acceso` |
| 504.5 | Duplicado matrícula en misma materia | Ignorar sin error (backlog) |
| 504.6 | Docente solo su materia | `GetMateriaById` + comparar `docente_id` |

**Formato columnas:** matrícula, nombre, email, tipo formación (spec MS3).

---

### ISSUE-505 — Gestión alumnos por materia

| # | Tarea | Criterio |
|---|--------|----------|
| 505.1 | `GET /alumnos/materia/:materiaId` | Solo activos |
| 505.2 | `GET /alumnos/:id` | Autorización admin / docente titular / self |
| 505.3 | Paginación | §5.4.5 |

---

### ISSUE-506 — Baja de materia

| # | Tarea | Criterio |
|---|--------|----------|
| 506.1 | `DELETE /alumnos/:id/baja` con `materia_id` en body (spec) o path acordado | Solo alumno autenticado = `:id` |
| 506.2 | Verificar `baja_solicitada` false | 400 si ya baja |
| 506.3 | Marcar inscripción inactiva + fechas | No borrar fila |
| 506.4 | `SendBajaNotif` | Incluir `docente_id` (usuario o entidad docente — alinear con proto MS-6) |
| 506.5 | Efecto downstream | MS-4/MS-5 ven alumno fuera vía `IsAlumnoEnMateria` |

---

### ISSUE-507 — Servidor gRPC (50053)

| # | Tarea | Criterio |
|---|--------|----------|
| 507.1 | Implementar 4 RPC del proto | Tests grpcurl |
| 507.2 | `IsAlumnoEnMateria` | `false` si baja o inactivo |
| 507.3 | Performance | `GetAlumnosByMateria` con muchos alumnos: queryset optimizado |

---

### ISSUE-508 — `GET /alumnos/me/materias`

| # | Tarea | Criterio |
|---|--------|----------|
| 508.1 | Rol alumno | 403 otros roles |
| 508.2 | Enriquecer con MS-2 | NRC, nombre materia, sección, nombre docente |
| 508.3 | Solo inscripciones activas | |

---

### ISSUE-509 — JWT MS-3

| # | Tarea | Criterio |
|---|--------|----------|
| 509.1 | Mismo patrón que MS-2 | Decorador reutilizable o paquete común `libs/agm_auth/` si el equipo extrae |

---

## 6. Seguridad

| Tema | Regla |
|------|--------|
| API interna | Si MS-3 expone `POST` creación masiva, proteger con API key MS↔MS donde aplique |
| Alumno baja | No permitir baja en nombre de otro alumno |
| PII | Logs sin emails completos en prod |

---

## 7. Matriz de pruebas

| ID | Caso | Esperado |
|----|------|------------|
| A1 | Import docente duplicado | Update, no doble usuario |
| A2 | Preview import alumnos | Sin filas en BD |
| A3 | Confirm import | Usuario MS-1 + inscripción + correo (mock o real) |
| A4 | Baja segunda vez | 400 |
| A5 | Docente lista otra materia | 403 |
| A6 | gRPC `GetAlumnosByMateria` | Sin bajas |

---

## 8. Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Seeds 300k+ alumnos | Carga en entorno controlado; índices; no bloquear demo |
| MS-1 caído en import | Rollback parcial; respuesta con resumen de fallos |
| Desalineación `docente_id` MS-2 vs MS-3 | Convención: mismo ID entidad docente en ambos lados |

---

## 9. Checklist salida Epic 5

- [ ] ISSUE-501 … 509.  
- [ ] `proto/alumnos.proto` completo.  
- [ ] Flujo video: import docentes + import alumnos + baja.  
- [ ] Postman carpeta MS-3.  

---

## 10. Referencias

- `docs/backlog_AGM_completo.md` — Epic 5  
- `docs/Proyecto_Final_SW_AGM.md` — §5.2, §5.3  
- `docs/microservicios/MS3_DOCENTES_ALUMNOS.md`  
- `test-data/` — seeds BUAP  
- `proto/alumnos.proto`  
