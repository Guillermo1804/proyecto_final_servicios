# Pruebas frontend — MS-3 Docentes & Alumnos

## Requisitos previos

```bash
docker compose up -d rabbitmq db-auth ms-auth ms-auth-event-consumer ms-auth-outbox-worker \
  db-periodos ms-periodos db-alumnos ms-alumnos ms-alumnos-outbox-worker nginx
```

**Importante:** con `USE_EVENT_BUS=true`, MS-3 **no usa gRPC** hacia Auth. Al **importar alumnos** se llama a MS-1 por HTTP interno; si MS-1 esta caido, quedan sin `usuario_id` y el boton **Activar** en la lista permite reintentar. **Docentes** siguen importandose sin activar (boton Activar en admin).

En `ms-alumnos/.env` y `ms-auth/.env` la misma clave:

```env
INTERNAL_API_KEY=cambiar-en-produccion
MS_AUTH_HTTP_URL=http://ms-auth:8001
```

Sin `ms-auth-event-consumer` el import por eventos puede tardar; **Activar** en admin es la via directa.

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
| 2 | Buscar | `?buscar=` coincide en nombre, apellido, correo o departamento (ej. Mendes, Ruiz, Yael) |
| 3 | Importar PDF | Boton "Importar Docentes (PDF)" → `POST /docentes/importar/` |
| 4 | Eliminar | `DELETE /docentes/{id}/` con confirmacion |
| 5 | Estado | Activo = tiene `usuario_id` en MS-1; Inactivo = sin vinculo |
| 6 | Activar | Clic en **Activar** (Inactivo) → `POST /docentes/{id}/activar-usuario/` crea o vincula usuario MS-1 |

**Nota:** Tras activar, login docente con su correo; contraseña inicial = parte antes de `@`.

**Login tras import (docentes/alumnos nuevos):** contraseña inicial = parte del correo **antes de `@`** (ej. `maria.garcia@correo.buap.mx` → `maria.garcia`). Espera a que el consumer de MS-1 cree el usuario (`usuario_id` en lista = Activo) y prueba en `/login` con ese email y contraseña.

---

## Docente — Mis materias (`/docente/materias`)

| # | Prueba | Esperado |
|---|--------|----------|
| 1 | Login docente | Usuario con registro en `docentes` (`usuario_id` = id MS-1) |
| 2 | Lista materias | Periodo activo (MS-2) + `GET /materias/?periodo_id=` + filtro por nombre del docente (MS-3) |
| 3 | Periodo en pantalla | Muestra el periodo **activo** (ej. Otono), no texto fijo |
| 4 | Sin materias | Mensaje claro si no hay match de nombre con el PDF |

---

## Docente — Detalle materia / alumnos (`/docente/materias/{nrc}`)

| # | Prueba | Esperado |
|---|--------|----------|
| 1 | Tab alumnos | `GET /alumnos/por-materia/?materia_id=` (resuelve NRC via MS-2) |
| 2 | Sin inscripciones | Lista vacia (no mock) |
| 3 | Import lista clase | Al confirmar import, cada alumno intenta **activarse en MS-1** al vuelo (HTTP interno) |
| 4 | Columna MS-1 | Por defecto **Desactivar** (vinculado); **Activar** solo si fallo MS-1 al importar |
| 5 | Desactivar alumno | `POST /alumnos/{id}/desactivar-usuario/` — `activo=false` en MS-1 y `usuario_id` null en MS-3 |
| 6 | Reactivar (respaldo) | `POST /alumnos/{id}/activar-usuario/` si quedo sin usuario tras caida de MS-1 |

Evaluacion / actividades / calificaciones en detalle materia: MS-4 (ver `PRUEBAS_MS4_CALIFICACIONES.md`).

---

## Docente — Importar alumnos (`/docente/materias/{nrc}/importar-alumnos`)

| # | Prueba | Esperado |
|---|--------|----------|
| 1 | Resolver materia | NRC de la ruta → `materia_id` (MS-2, periodo activo) |
| 2 | Subir PDF lista de clase | Al elegir archivo → `POST /alumnos/importar/preview/` (`file`, `materia_id`) |
| 3 | Vista previa | Tabla: matricula, nombre, email, accion (Nuevo/Actualizar), inscripcion (5 por pagina) |
| 4 | Confirmar | `POST /alumnos/importar/confirmar/` JSON: `materia_id`, `alumnos` (filas de la preview) |
| 5 | Resumen | `creados`, `actualizados`, `inscritos` |

PDF: exportar desde **Servicios Web → Lista de clase** (Ctrl+P). Debe traer `NRC:` y filas con matricula `20XXXXXXXX` (como `ListaAlumnos_Servicios_Web.pdf` en la raiz del repo).

El correo **no aparece como texto** en el PDF (al imprimir desde Chrome), pero sí en **enlaces `mailto:`** (icono de correo). El parser de MS-3 los lee con pdfplumber y crea el usuario en MS-1 con ese email. Si faltan enlaces, fallback `{matricula}@alumno.buap.mx`.

---

## Alumno — Dashboard, perfil y horario

| Ruta | API |
|------|-----|
| `/alumno/dashboard` | `GET /alumnos/me/` (perfil) + `GET /alumnos/me/materias/` |
| `/alumno/perfil` | `GET /alumnos/me/` |
| `/alumno/horario` | `GET /alumnos/me/materias/` (horario por dia) |

Si el alumno fue importado antes de crear usuario MS-1, el primer acceso **vincula** `usuario_id` por email o matricula en el correo (`202228369@alumno.buap.mx`).

Login con usuario **alumno** que tenga registro en tabla `alumnos` e inscripciones.

---

## Endpoints MS-3 usados

| Accion | Metodo | URL |
|--------|--------|-----|
| Listar docentes | GET | `/docentes/` |
| Importar docentes PDF | POST | `/docentes/importar/` |
| Eliminar docente | DELETE | `/docentes/{id}/` |
| Activar docente (MS-1) | POST | `/docentes/{id}/activar-usuario/` |
| Activar alumno (MS-1, respaldo) | POST | `/alumnos/{id}/activar-usuario/` |
| Desactivar alumno (MS-1) | POST | `/alumnos/{id}/desactivar-usuario/` |
| Alumnos por materia | GET | `/alumnos/por-materia/?materia_id=` |
| Perfil alumno (MS-3) | GET | `/alumnos/me/` |
| Mis materias (alumno) | GET | `/alumnos/me/materias/` |
| Vista previa import alumnos | POST | `/alumnos/importar/preview/` (`file`, `materia_id`) |
| Confirmar import alumnos | POST | `/alumnos/importar/confirmar/` (`materia_id`, `alumnos[]`) |
| Importar alumnos PDF (directo) | POST | `/alumnos/importar/` (`file`, `materia_id`) |

---

## Problemas comunes

| Sintoma | Solucion |
|---------|----------|
| 401 | Iniciar sesion; token en sessionStorage |
| Docente sin materias | Crear docente con `usuario_id` y materias en MS-2 con su nombre |
| Activar 400 gRPC deshabilitado | Rebuild `ms-alumnos` + `INTERNAL_API_KEY` en `.env` de MS-3 = MS-1 |
| Alumno sin horario | Inscripciones activas en MS-3 + login alumno |
| 403 en import | Requiere rol **admin** o **docente** |
| materia_id 400 | Enviar ID de materia MS-2, no solo NRC en la URL |

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
