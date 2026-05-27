# Despliegue en Railway — ISSUE-106 (Epic 1)

Guía para publicar los **7 microservicios** con HTTPS. El frontend Angular se despliega aparte (Vercel/Netlify); aquí solo backend.

## 1. Preparación

1. Cuenta en [Railway](https://railway.app) y repositorio GitHub conectado.
2. En **producción**, en cada MS (variables del panel Railway):
   - `DEBUG=False`
   - `CORS_ALLOW_ALL_ORIGINS=False`
   - `CORS_ALLOWED_ORIGINS=https://TU-FRONTEND.vercel.app,https://TU-GATEWAY.up.railway.app`
   - `SECRET_KEY` único y largo (generar con `python -c "import secrets; print(secrets.token_urlsafe(50))"`)
   - `ALLOWED_HOSTS=*.up.railway.app,tu-dominio.com`

## 2. Base de datos MySQL por MS

En Railway, por cada microservicio:

1. **New → Database → MySQL**
2. Vincular la BD al servicio del MS correspondiente.
3. Mapear variables (Railway suele inyectar `MYSQLHOST`, etc.). Ajustar a los nombres del proyecto:

| Variable AGM | Origen típico Railway |
|--------------|------------------------|
| `DB_HOST` | `${{MySQL.MYSQLHOST}}` o host del plugin |
| `DB_PORT` | `3306` |
| `DB_NAME` | `agm_auth_db` (una BD lógica por MS) |
| `DB_USER` | usuario del plugin |
| `DB_PASSWORD` | password del plugin |

## 3. Servicio web por microservicio

Por cada carpeta `ms-*`:

1. **New → GitHub Repo** → mismo repo, **Root Directory** = `ms-auth` (repetir para cada MS).
2. **Build:** Dockerfile en la raíz del MS (ya incluido).
3. **Start command:** usa el `entrypoint.sh` del Dockerfile (por defecto).
4. **Networking → Public domain** → copiar URL HTTPS.
5. **Variables:** copiar desde `ms-*/.env.example` y completar hosts gRPC con las URLs internas de Railway o nombres de servicio si usas Railway private networking.

Puertos a exponer en Railway:

| MS | REST | gRPC (interno) |
|----|------|----------------|
| MS-1 | 8001 | 50051 |
| … | … | … |
| MS-7 | 8007 | 50057 |

## 4. Redis (MS-5)

Crear plugin **Redis** y enlazarlo a `ms-asistencias`. Configurar `REDIS_URL` según `ms-asistencias/.env.example`.

## 5. API Gateway en producción

Opciones:

- **A)** Un servicio Nginx con `docker/nginx/default.conf` y variables upstream apuntando a las 7 URLs Railway.
- **B)** Exponer cada MS por su URL y configurar el frontend con lista de bases (menos alineado al enunciado).

Recomendado: **un servicio `nginx`** en Railway con el mismo `default.conf`, sustituyendo hosts `ms-auth` por URLs privadas o públicas según red Railway.

## 6. Smoke test remoto

```bash
curl -s https://TU-MS-AUTH.up.railway.app/health/
curl -s -o /dev/null -w "%{http_code}" -X POST https://TU-GATEWAY/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@agm.buap.mx","password":"admin123"}'
```

## 7. Actualizar README

Sustituir la tabla **URLs de Producción** en `README.md` con las URLs reales de Railway al terminar cada despliegue.

## Checklist ISSUE-106

- [ ] 7 servicios web desplegados
- [ ] 7 BDs MySQL (o esquemas aislados)
- [ ] HTTPS activo en cada URL
- [ ] Variables solo en Railway (no en Git)
- [ ] README actualizado
- [ ] CORS de producción sin `ALLOW_ALL`
