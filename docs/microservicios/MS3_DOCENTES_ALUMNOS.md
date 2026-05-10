# 👥 MS-3: Docentes & Alumnos — Especificación para IA

> **Lee primero**: `docs/CONTEXTO_GLOBAL_PROYECTO.md`

---

## Identidad

| Campo | Valor |
|-------|-------|
| **Carpeta** | `/ms-alumnos/` |
| **Puerto REST** | 8003 |
| **Puerto gRPC** | 50053 |
| **BD** | MySQL – `agm_alumnos_db` |
| **Responsabilidad** | Importación PDF directorio docente, CRUD docentes, importación Excel alumnos, inscripciones, baja de materia |

## Dependencias extras
```
pdfplumber>=0.10
openpyxl>=3.1
pandas>=2.2
```

## Modelos

### `Docente`
- `usuario_id` (IntegerField, unique) — ID en MS-1 Auth
- `nombre` (CharField 255)
- `email_institucional` (EmailField, unique)
- `cubiculo` (CharField 50, nullable)

### `Alumno`
- `usuario_id` (IntegerField, unique) — ID en MS-1 Auth
- `matricula` (CharField 20, unique) — Ej: "202012345"
- `nombre` (CharField 255)
- `email` (EmailField)
- `tipo_formacion` (CharField 100, blank) — Ej: "Licenciatura"

### `InscripcionMateria`
- `alumno` (FK → Alumno)
- `materia_id` (IntegerField) — ID en MS-2
- `fecha_inscripcion` (DateTimeField auto_now_add)
- `activo` (BooleanField, default=True) — False = dado de baja
- `baja_solicitada` (BooleanField, default=False) — True = irreversible
- `fecha_baja` (DateTimeField, null)
- **unique_together**: `['alumno', 'materia_id']`

## Datos Pre-cargados: Bases de Datos BUAP

> **IMPORTANTE**: El equipo cuenta con bases de datos reales de la BUAP:
> - **43,025 trabajadores** (13,157 con email) → para pre-cargar docentes
> - **318,374 alumnos** (316,807 con email) → para pre-cargar alumnos

### Archivos de DOCENTES en `test-data/`
| Archivo | Formato | Registros | Uso |
|---------|---------|-----------|-----|
| `buap_trabajadores.db` | SQLite | 43,025 | BD original, consultas con Python |
| `trabajadores_buap.csv` | CSV | 43,025 | Universal, abrir en Excel |
| `seed_docentes_mysql.sql` | SQL (MySQL) | 13,157 | INSERT directo a MySQL |
| `export_trabajadores.py` | Python | — | Script para regenerar CSV y SQL |

### Archivos de ALUMNOS en `test-data/`
| Archivo | Formato | Registros | Uso |
|---------|---------|-----------|-----|
| `buap_alumnos.db` | SQLite | 318,374 | BD original, consultas con Python |
| `alumnos_buap.csv` | CSV | 318,374 | Universal, abrir en Excel |
| `seed_alumnos_mysql.sql` | SQL (MySQL) | 316,807 | INSERT directo a MySQL (bloques de 1000) |
| `export_alumnos.py` | Python | — | Script para regenerar CSV y SQL |

### Estructura de los datos (igual para ambas BDs)
| Campo BD | Tipo | Ejemplo (docente) | Ejemplo (alumno) |
|----------|------|-------|-------|
| `matricula` | INTEGER | 100000004 | 202000000 |
| `paterno` | TEXT | PEREZ | SOSA |
| `materno` | TEXT | BONILLA | JUAREZ |
| `nombre` | TEXT | EVELIA | MARISOL |
| `email` | TEXT | evelia.perez@correo.buap.mx | marisol.sosaj@alumno.buap.mx |

### Cómo usarlas
```bash
# Después de correr migraciones de MS-3
mysql -u root -p agm_alumnos_db < test-data/seed_docentes_mysql.sql
mysql -u root -p agm_alumnos_db < test-data/seed_alumnos_mysql.sql
```

> **Nota**: Los endpoints de importación (PDF para docentes, Excel para alumnos) siguen siendo
> necesarios para la evaluación. Los datos pre-cargados sirven para tener datos desde el día 1.

---

## Endpoints REST

### Docentes
- `POST /docentes/importar` — Auth: admin. Upload PDF directorio institucional.
  - Parsear con pdfplumber: nombre, email, cubículo
  - Por cada docente nuevo: gRPC a MS-1 `CreateUser(email, nombre, rol='docente', password=uuid)`
  - Guardar en BD local con usuario_id
  - Manejar duplicados por email

- `POST /docentes/seed` — Auth: admin. **Endpoint adicional** para cargar docentes desde el CSV/SQLite pre-existente.
  - Lee `test-data/trabajadores_buap.csv` o recibe el CSV como upload
  - Crea usuarios en MS-1 y docentes en BD local
  - Útil para inicialización rápida del sistema

- `GET /docentes` — Auth: admin. Paginado con búsqueda.
- `GET /docentes/:id` — Auth: admin o el propio docente
- `PUT /docentes/:id` — Auth: admin
- `POST /docentes/:id/reset-password` — Auth: admin → gRPC a MS-1

### Alumnos
- `POST /alumnos/importar/:materiaId` — Auth: docente de la materia. Upload Excel/CSV.
  - Si `?preview=true`: retornar vista previa sin guardar
  - Confirmar: parsear, crear usuario (gRPC MS-1), guardar alumno, inscribir, enviar correo (gRPC MS-6 SendBienvenida)
  - Manejar duplicados por matrícula

- `GET /alumnos/materia/:materiaId` — Auth: docente de la materia. Solo alumnos activos (no dados de baja).
- `GET /alumnos/:id` — Auth: docente, admin, o el propio alumno
- `DELETE /alumnos/:id/baja` — Auth: alumno (solo el propio). Body: `{materia_id}`
  - Verificar inscripción activa
  - Verificar `baja_solicitada == False`
  - Marcar activo=False, baja_solicitada=True, fecha_baja=now
  - gRPC a MS-6 `SendBajaNotif`
  - **IRREVERSIBLE**: retornar 400 si ya solicitó baja antes

- `GET /alumnos/me/materias` — Auth: alumno. Sus materias activas con datos de MS-2 via gRPC.

## Servidor gRPC (Puerto 50053)
```protobuf
syntax = "proto3";
package alumnos;
service AlumnosService {
  rpc GetAlumnosByMateria(GetAlumnosByMateriaRequest) returns (AlumnosListResponse);
  rpc GetAlumnoById(GetAlumnoByIdRequest) returns (AlumnoInfo);
  rpc IsAlumnoEnMateria(IsAlumnoEnMateriaRequest) returns (IsAlumnoEnMateriaResponse);
  rpc GetDocenteByUsuarioId(GetDocenteByUsuarioIdRequest) returns (DocenteInfo);
}
// GetAlumnosByMateria: materia_id → lista de AlumnoInfo (solo activos)
// GetAlumnoById: alumno_id → AlumnoInfo
// IsAlumnoEnMateria: alumno_id + materia_id → bool (true solo si activo y no dado de baja)
// GetDocenteByUsuarioId: usuario_id → DocenteInfo
```

## Clientes gRPC
| Destino | Método | Cuándo |
|---------|--------|--------|
| MS-1 | ValidateToken, CreateUser | Auth + crear usuarios al importar |
| MS-2 | GetMateriaById | Dashboard alumno, validar docente de materia |
| MS-6 | SendBienvenida, SendBajaNotif | Correos al importar/dar de baja |

## Reglas Críticas
1. Baja IRREVERSIBLE: una vez `baja_solicitada=True` no se revierte
2. Alumnos dados de baja NO aparecen en listados, concentrado ni pase de lista
3. Al importar, si matrícula ya existe → reutilizar, no duplicar
4. Solo el docente asignado puede ver/importar alumnos de su materia
5. El correo de bienvenida solo se envía la primera vez
6. Excel mínimo: matrícula, nombre, email

## Formato Excel esperado

| Matrícula | Nombre | Email | Tipo de Formación |
|-----------|--------|-------|-------------------|
| 202012345 | Juan Pérez | juan@alumno.buap.mx | Licenciatura |
