# Pruebas frontend ↔ MS-6 (Notificaciones / correo)

MS-6 **no expone pantallas propias** en Angular. El frontend dispara flujos en MS-1, MS-3 y MS-4; esos servicios publican eventos y **MS-6** envía el correo por SMTP.

## Infraestructura

```bash
docker compose up -d rabbitmq db-notificaciones ms-notificaciones ms-notificaciones-worker-consumer \
  ms-auth ms-auth-outbox-worker ms-alumnos ms-alumnos-outbox-worker \
  ms-calificaciones ms-calificaciones-outbox-worker nginx
```

En `ms-notificaciones/.env` (no commitear secretos):

- `EMAIL_HOST_USER=sistemasagm2026@gmail.com`
- `EMAIL_HOST_PASSWORD=` contraseña de aplicación de Google (16 caracteres, sin espacios)
- **No** usar `EMAIL_BACKEND=locmem` en Docker si quieres correo real (por defecto SMTP).

Reiniciar tras cambiar SMTP:

```bash
docker compose restart ms-notificaciones ms-notificaciones-worker-consumer
```

Prueba rápida SMTP:

```bash
docker exec agm-ms-notificaciones python manage.py send_test_email --to tu-correo@gmail.com
```

Frontend: `cd frontend/sistema_AGM && npm start` (proxy `/notificaciones` → gateway `:8080`).

## Mapa flujo UI → correo

| Pantalla / ruta | Acción usuario | API frontend | Evento → MS-6 | Tipo correo |
|-----------------|----------------|--------------|---------------|-------------|
| `/forgot-password` | Solicitar enlace | `POST /auth/forgot-password` | `password.reset_requested.v1` | Reset password |
| `/reset-password?token=` | Nueva contraseña | `POST /auth/reset-password` | — (solo MS-1) | — |
| `/docente/materias/{nrc}/importar-alumnos` | Confirmar import | `POST /alumnos/importar/confirmar/` | `alumno.imported.v1` | Bienvenida + clave |
| `/alumno/notas` | Dar de baja | `POST /alumnos/{id}/baja-materia/` | `alumno.withdrawn.v1` | Aviso al docente |
| Detalle materia → Cerrar | Cerrar materia | `POST /materias/{id}/cerrar` | `materia.calificaciones_cerradas.v1` | Cierre a alumnos |

## Datos de prueba (quecholacdavid11@gmail.com)

Configuración lista en Docker para recibir **todos** los tipos de correo en tu Gmail:

| Rol | Login | Contraseña | Notas |
|-----|-------|------------|--------|
| Alumno | `quecholacdavid11@gmail.com` | `quecholacdavid11` | MS-1 id 175 · matrícula `2026999123` · inscrito en materia **1** (NRC 50030) |
| Docente | `quecholacdavid11+docente@gmail.com` | `quecholacdavid11` | MS-1 id 176 · mismo buzón Gmail (`+docente` es alias) |

El docente en MS-3 usa `quecholacdavid11@gmail.com` para que el correo de **baja** también llegue a tu bandeja.

---

## Casos de prueba

### 1. Recuperar contraseña (MS-1 → MS-6)

1. Ir a `/forgot-password`.
2. Ingresar un email que exista en MS-1 (ej. `admin@agm.buap.mx` o un alumno importado).
3. Mensaje: «Si el correo existe, recibirás un enlace…».
4. Revisar bandeja (y spam). Enlace: `http://localhost:4200/reset-password?token=...`.
5. Abrir enlace, definir contraseña en `/reset-password`.
6. Verificar historial (opcional):

```bash
docker exec agm-ms-notificaciones python manage.py shell -c \
  "from apps.notificaciones.models import HistorialCorreo; print(HistorialCorreo.objects.filter(tipo='reset_password').order_by('-id')[:3].values('destinatario_email','exitoso'))"
```

Requiere: `ms-auth-outbox-worker`, `ms-notificaciones-worker-consumer`, `FRONTEND_URL=http://localhost:4200` en MS-1 y MS-6.

### 2. Bienvenida al importar alumnos (MS-3 → MS-6)

1. Login docente → importar lista PDF con emails `mailto:` válidos.
2. Confirmar importación.
3. Alumno nuevo debe recibir correo con clave de acceso (parte del email antes de `@` si MS-1 la generó así).
4. Comprobar outbox MS-3 y consumer MS-6 en logs si no llega el correo.

### 3. Baja de materia (alumno → MS-6)

1. Login alumno con inscripción activa → `/alumno/notas`.
2. «Dar de baja» → escribir `DARSE DE BAJA`.
3. Docente de la materia debe recibir correo (email del docente en MS-3 / evento).

### 4. Cierre de materia (MS-4 → MS-6)

1. Login docente → detalle materia → **Cerrar materia** (evaluación).
2. Confirmar diálogo.
3. Cada alumno inscrito activo debe recibir correo de cierre (puede tardar segundos si hay muchos).

## Endpoints MS-6 (solo pruebas / Postman)

El front **no** llama estos paths en producción; requieren `X-Internal-Api-Key`:

| Método | URL |
|--------|-----|
| POST | `/notificaciones/bienvenida` |
| POST | `/notificaciones/baja` |
| POST | `/notificaciones/cierre-materia` |
| POST | `/notificaciones/reset-password` |
| GET | `/notificaciones/health/` vía gateway → health del servicio |

## Problemas comunes

| Síntoma | Solución |
|---------|----------|
| Forgot-password OK pero sin correo | `EMAIL_BACKEND` no debe ser `locmem`; reiniciar MS-6; revisar consumer y `ms-auth-outbox-worker` |
| Import OK sin bienvenida | Evento sin `clave_acceso`; alumno sin usuario MS-1; revisar `ms-alumnos-outbox-worker` |
| Gmail rechaza SMTP | Usar contraseña de aplicación; cuenta con 2FA |
| Enlace reset abre mal | `FRONTEND_URL=http://localhost:4200` en MS-1 |
| 401 en Postman a MS-6 | Header `X-Internal-Api-Key` igual que `INTERNAL_API_KEY` en `.env` |

## Archivos frontend relacionados

- `src/app/services/auth.service.ts` — forgot / reset (MS-1)
- `src/app/services/recuperacion-password-services/recuperacion-password.service.ts`
- `src/app/screens/forgot-password-screen/`, `reset-password-screen/`
- `src/app/screens/docente-screen/importar-alumnos-screen/`
- `src/app/screens/alumno-screen/notas-screen/` — baja
- `src/app/screens/docente-screen/detalle-materia-screen/` — cerrar materia
- `proxy.conf.json` — prefijo `/notificaciones`
