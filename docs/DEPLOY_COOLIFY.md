# Despliegue AGM — Docker (Ubuntu / Coolify)

Stack **completo** en un solo `docker-compose.yml`:

| Capa | Servicios |
|------|-----------|
| Infra | RabbitMQ, Redis, 7× MySQL |
| API | MS-1 … MS-7 (REST + gRPC) |
| Workers | 5 outbox + 7 consumers (event bus) |
| Entrada | **nginx** (Angular + API en el mismo puerto) |

El archivo `docker-compose.ms1-4.yml` (solo MS-1…4) **ya no se usa** en despliegue; era solo para pruebas locales.

---

## Requisitos en el servidor

- Ubuntu 22.04+ (o similar)
- Docker Engine 24+ y plugin Compose V2 (`docker compose version`)
- Git
- Mínimo **4 GB RAM** recomendado (7 MySQL + workers)
- El host expone **80/443** solo en el servicio **caddy** (`docker-compose.prod.yml`); Caddy hace TLS y reenvía a `nginx:80`

---

## 1. Clonar y preparar `.env`

```bash
git clone <tu-repo> proyecto_final_servicios
cd proyecto_final_servicios

cp .env.example .env
for d in ms-auth ms-periodos ms-alumnos ms-calificaciones ms-asistencias ms-notificaciones ms-reportes; do
  cp "$d/.env.example" "$d/.env"
done
```

Edita cada `ms-*/.env`:

- `SECRET_KEY`, `JWT_*` en **ms-auth**
- `EMAIL_*` / SMTP en **ms-notificaciones** (correos reales)
- `DB_HOST=db-<servicio>` (nombre del servicio Compose, **no** `localhost`)
- Hosts gRPC: `ms-auth`, `ms-periodos`, etc.

En `.env` de la raíz (RabbitMQ):

```env
RABBITMQ_PASSWORD=<password_fuerte>
```

---

## 2. Levantar en producción

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Primera vez (migraciones y proyecciones):

```bash
docker compose exec ms-auth python manage.py migrate
docker compose exec ms-periodos python manage.py migrate
docker compose exec ms-alumnos python manage.py migrate
docker compose exec ms-calificaciones python manage.py migrate
docker compose exec ms-calificaciones python manage.py backfill_calificaciones_projections
docker compose exec ms-asistencias python manage.py migrate
docker compose exec ms-notificaciones python manage.py migrate
docker compose exec ms-reportes python manage.py migrate
```

Verifica:

- Desde el servidor (red Docker): `docker compose exec nginx wget -qO- http://127.0.0.1/health`
- En el navegador: `https://agm.aurelyte.iokoia.com/` (o el valor de `AGM_DOMAIN` en `.env`; certificado vía Caddy/Let's Encrypt)
- El front en producción usa `apiBaseUrl: ''` (mismo origen que el gateway)

---

## 3. Coolify

1. **New Resource** → Docker Compose
2. Repositorio Git + rama
3. **Compose file**: `docker-compose.yml`
4. **Additional compose file** (si Coolify lo permite): `docker-compose.prod.yml`
5. Variables de entorno: copia `.env` raíz y las de cada `ms-*` (o un `.env` por servicio en la UI)
6. Si usas el **Caddy del stack** (`docker-compose.prod.yml`), no configures proxy SSL en Coolify: el dominio `AGM_DOMAIN` debe resolver al servidor y Caddy ocupará 80/443.
7. Alternativa sin Caddy en el stack: dominio → servicio **nginx**, puerto **80**, SSL en Coolify (deja comentado o no levantes el servicio `caddy`).

En el firewall no expongas 13307–13313, 8001–8007 ni 5672/15672.

---

## 4. Desarrollo local (Windows)

```powershell
.\scripts\copy-env.ps1
.\scripts\start-full-stack.ps1
```

- App: http://localhost:8080 (solo con `docker-compose.dev.yml`; no uses `AGM_HTTP_PORT=80`)
- MySQL debug: puertos 13307–13313 (solo en `docker-compose.yml` base, no en prod)

---

## 5. Comandos útiles

```bash
docker compose ps
docker compose logs -f nginx ms-auth
docker compose restart nginx
docker compose down
docker compose down -v   # borra volúmenes (BD)
```

---

## Arquitectura de red

Todo en `agm-network`. En producción con Caddy: navegador → **caddy** (443) → **nginx** (80 interno). Nginx:

- Sirve el build de `frontend/sistema_AGM`
- Enruta `/auth`, `/materias`, `/calificaciones`, etc. a cada MS

Los workers RabbitMQ no exponen puertos al host.
