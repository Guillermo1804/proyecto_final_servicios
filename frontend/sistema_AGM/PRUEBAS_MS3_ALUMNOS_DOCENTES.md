# Pruebas frontend — MS-3 Docentes & Alumnos

## Requisitos previos

```bash
docker compose up -d rabbitmq db-auth ms-auth ms-auth-event-consumer ms-auth-outbox-worker \
  db-periodos ms-periodos db-alumnos ms-alumnos ms-alumnos-outbox-worker nginx
```

**Importante:** sin `ms-auth-event-consumer` los docentes quedan sin usuario en MS-1 y el login falla. Levanta el consumer **antes** de importar el PDF (o reinicia la cola si reimportas).

Frontend:

```bash
cd frontend/sistema_AGM
npm start
```

Login segun rol a probar (admin / docente / alumno con datos en BD).

---

## Admin — Docentes (`/admin/docentes`)

| # | Prueba | Esperado |
|---|--------|----------|
| 1 | Listar docentes | `GET /docentes/?page=&limit=` datos reales |
| 2 | Buscar | Filtro por nombre o busqueda local |
| 3 | Importar PDF | Boton "Importar Docentes (PDF)" → `POST /docentes/importar/` |
| 4 | Eliminar | `DELETE /docentes/{id}/` con confirmacion |
| 5 | Estado | Activo = tiene `usuario_id` en MS-1; Inactivo = pendiente |

**Nota:** No hay toggle de estado en API; solo lectura del vinculo con MS-1.

**Login tras import (docentes/alumnos nuevos):** contraseña inicial = parte del correo **antes de `@`** (ej. `maria.garcia@correo.buap.mx` → `maria.garcia`). Espera a que el consumer de MS-1 cree el usuario (`usuario_id` en lista = Activo) y prueba en `/login` con ese email y contraseña.

---

## Docente — Mis materias (`/docente/materias`)

| # | Prueba | Esperado |
|---|--------|----------|
| 1 | Login docente | Usuario con registro en `docentes` (`usuario_id` = id MS-1) |
| 2 | Lista materias | `GET /docentes/?usuario_id=` + `GET /materias/?docente_nombre=` (MS-2) |

---

## Docente — Detalle materia / alumnos (`/docente/materias/{nrc}`)

| # | Prueba | Esperado |
|---|--------|----------|
| 1 | Tab alumnos | `GET /alumnos/por-materia/?materia_id=` (resuelve NRC via MS-2) |
| 2 | Sin inscripciones | Lista vacia (no mock) |

Evaluacion / actividades / calificaciones siguen en UI local (MS-4 en siguiente integracion).

---

## Docente — Importar alumnos (`/docente/materias/{nrc}/importar-alumnos`)

| # | Prueba | Esperado |
|---|--------|----------|
| 1 | Subir Excel/CSV | `POST /alumnos/importar/preview/` |
| 2 | Ver preview | Tabla con filas validas |
| 3 | Confirmar | `POST /alumnos/importar/confirmar/` con body `{ alumnos: [...] }` |

Columnas requeridas en archivo: `matricula`, `nombre`, `apellido`, `email`.

---

## Alumno — Perfil y horario

| Ruta | API |
|------|-----|
| `/alumno/perfil` | `GET /auth/me` + `GET /alumnos/me/materias/` (rol alumno) |
| `/alumno/horario` | `GET /alumnos/me/materias/` |

Login con usuario **alumno** que tenga registro en tabla `alumnos` e inscripciones.

---

## Endpoints MS-3 usados

| Accion | Metodo | URL |
|--------|--------|-----|
| Listar docentes | GET | `/docentes/` |
| Importar docentes PDF | POST | `/docentes/importar/` |
| Eliminar docente | DELETE | `/docentes/{id}/` |
| Alumnos por materia | GET | `/alumnos/por-materia/?materia_id=` |
| Mis materias (alumno) | GET | `/alumnos/me/materias/` |
| Preview import | POST | `/alumnos/importar/preview/` |
| Confirmar import | POST | `/alumnos/importar/confirmar/` |

---

## Problemas comunes

| Sintoma | Solucion |
|---------|----------|
| 401 | Iniciar sesion; token en sessionStorage |
| Docente sin materias | Crear docente con `usuario_id` y materias en MS-2 con su nombre |
| Alumno sin horario | Inscripciones activas en MS-3 + login alumno |
| 403 en import | Solo **admin** puede importar alumnos (preview/confirmar) |

---

## Archivos frontend (MS-3)

- `src/app/models/alumnos-api.model.ts`
- `src/app/services/alumno-services/alumnos.service.ts`
- `src/app/services/admin-services/docentes.service.ts`
- `src/app/services/docente-services/importar-alumnos.service.ts`
- `src/app/services/docente-services/materias-docente.service.ts`
- `src/app/services/docente-services/detalle-materia-docente.service.ts`
- `src/app/services/alumno-services/perfil.service.ts`
- `src/app/services/alumno-services/horario.service.ts`
- Pantallas admin/docente/alumno relacionadas
