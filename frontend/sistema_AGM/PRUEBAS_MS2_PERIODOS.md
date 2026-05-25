# Pruebas frontend — MS-2 Periodos & Materias

## Requisitos previos

1. Backend (MS-1 + MS-2 + gateway):

```bash
docker compose up -d rabbitmq db-auth ms-auth db-periodos ms-periodos nginx
```

Opcional outbox: `ms-periodos-outbox-worker`

2. Frontend:

```bash
cd frontend/sistema_AGM
npm install
npm start
```

3. Login como **admin** (`admin@agm.buap.mx` / `admin123`) — MS-2 exige JWT en casi todos los endpoints.

Gateway: **http://127.0.0.1:8080**

---

## Casos de prueba — Periodos

Ruta: **http://localhost:4200/admin/periodos**

| # | Accion | Resultado esperado |
|---|--------|-------------------|
| 1 | Abrir pantalla sin login | Redirige a `/login` |
| 2 | Listar periodos | Tabla con datos reales de `GET /periodos/` (no datos mock locales) |
| 3 | Crear periodo | Formulario temporada + anio + fechas → `POST /periodos/` → aparece en lista |
| 4 | Editar periodo | `PUT /periodos/{id}/` actualiza nombre y fechas |
| 5 | Activar periodo inactivo | `POST /periodos/{id}/activar/` — solo uno queda activo |
| 6 | Intentar “desactivar” el activo | Mensaje: debe activar otro periodo (no hay endpoint de desactivar directo) |
| 7 | Eliminar periodo sin materias | `DELETE` exitoso |
| 8 | Eliminar periodo con materias | Error 400 con mensaje del backend |
| 9 | Bloque periodo activo | Banner superior muestra el periodo activo (`GET /periodos/activo/`) |

Filtros **temporada** y **busqueda**: se aplican en el cliente sobre la lista (el API no los expone).

---

## Casos de prueba — Materias

Ruta: **http://localhost:4200/admin/materias**

| # | Accion | Resultado esperado |
|---|--------|-------------------|
| 1 | Sin periodo activo | Mensaje indicando que active un periodo primero |
| 2 | Con periodo activo | Lista `GET /materias/?periodo_id={id}&page=&limit=` |
| 3 | Buscar por NRC/clave/docente | Filtra resultados (param `nombre` + filtro local) |
| 4 | Paginacion | Botones anterior/siguiente segun `count` del API |
| 5 | Columnas | Docente desde `docente_nombre`; horario parseado en dias/hora |

El boton **Importar Materias** en UI aun no abre archivo; el endpoint existe: `POST /periodos/{id}/importar-materias/` (PDF).

---

## Endpoints MS-2 usados

| Accion | Metodo | URL (via Nginx) |
|--------|--------|-----------------|
| Listar periodos | GET | `/periodos/?page=1&limit=10` |
| Periodo activo | GET | `/periodos/activo/` |
| Crear periodo | POST | `/periodos/` |
| Actualizar | PUT | `/periodos/{id}/` |
| Eliminar | DELETE | `/periodos/{id}/` |
| Activar | POST | `/periodos/{id}/activar/` |
| Listar materias | GET | `/materias/?periodo_id=&page=&limit=` |
| Importar PDF | POST | `/periodos/{id}/importar-materias/` |

Respuesta tipica: `{ "success": true, "data": ..., "message": "OK" }`.

Listas paginadas de materias: `data.results` + `data.count`.

---

## Problemas comunes

| Sintoma | Solucion |
|---------|----------|
| 401 en periodos/materias | Iniciar sesion como admin; token en sessionStorage |
| 403 | Solo admin puede crear/editar/eliminar/activar periodos |
| Lista vacia de materias | Activar un periodo y cargar materias (seed o import PDF) |
| Error de conexion (status 0) | `docker compose ps` — `nginx`, `ms-periodos`, `ms-auth` |

---

## Archivos frontend tocados (MS-2)

- `src/app/services/tools/agm-api.helpers.ts` — envelope y URLs
- `src/app/models/periodos-api.model.ts`
- `src/app/services/admin-services/periodos.service.ts`
- `src/app/services/admin-services/materias.service.ts`
- `src/app/screens/admin-screen/periodos-screen/*`
- `src/app/screens/admin-screen/materias-screen/*`
