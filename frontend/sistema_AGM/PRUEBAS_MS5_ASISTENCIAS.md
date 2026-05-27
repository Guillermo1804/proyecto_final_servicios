# Pruebas frontend ↔ MS-5 (Asistencias QR)

## Proyecciones MS-5 (importante)

MS-5 valida periodo activo contra su **read model local**. Si activaste el periodo en Admin después de levantar Docker, ejecuta:

```bash
docker compose exec ms-asistencias python manage.py backfill_asistencias_projections
```

El consumer debe escuchar `periodo.activated.v1` (al activar periodo en MS-2). Reinicia el worker si cambiaste código:

```bash
docker compose restart ms-asistencias-worker-consumer
```

## Infraestructura

Levantar al menos MS-1…MS-3, **MS-5**, Redis y Nginx:

```bash
docker compose up -d ms-auth ms-periodos ms-alumnos ms-asistencias redis nginx
```

Tras cambiar `docker/nginx/default.conf`, recrear nginx:

```bash
docker compose up -d --force-recreate nginx
```

Frontend: `cd frontend/sistema_AGM && npm start` (proxy a `:8080`).

## Flujo docente (`/docente/asistencias`)

1. Login docente con materias asignadas.
2. Seleccionar materia → **Iniciar sesión** → `POST /sesiones/iniciar/`.
3. Alumno activa QR en perfil (misma materia, con sesión activa).
4. Escanear QR → `POST /asistencias/registrar/` con `encoded_payload`.
5. **Confirmar lista** → `POST /sesiones/{id}/confirmar/`.
6. **Historial / descargas** → `GET /sesiones/historial/?materia_id=` y botones CSV/PDF en la misma pantalla.

## Flujo alumno (`/alumno/perfil`)

1. Login alumno con inscripciones activas.
2. Elegir materia en el selector.
3. **Activar QR** → `GET /qr/generate/?materia_id=&alumno_id=` (renueva cada 5 s).
4. **Resumen de asistencia** → `GET /registros/stats_alumno_materia/?alumno_id=&materia_id=` (bloque «Mi asistencia»).

## Docente → Rendimiento

- Columna **Asistencia** usa `stats_alumno_materia` por alumno en riesgo.

## Rutas proxy (Angular → Nginx → MS-5)

| Prefijo | Backend |
|---------|---------|
| `/sesiones/` | `/api/sesiones/` |
| `/registros/` | `/api/registros/` |
| `/qr/` | `/api/qr/` |
| `/asistencias/` | `/api/asistencias/` |

## Archivos clave

- `src/app/services/asistencias.service.ts`
- `src/app/services/docente-services/asistencias-docente.service.ts`
- `src/app/services/alumno-services/qr-asistencia.service.ts`
- `src/app/screens/docente-screen/asistencias-screen/`
- `src/app/screens/alumno-screen/perfil-screen/`
