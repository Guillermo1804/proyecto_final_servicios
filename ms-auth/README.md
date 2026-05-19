# MS-1 — Auth & Users

Autenticación centralizada: JWT (access + refresh), RBAC, recuperación de contraseña vía MS-6, gestión de usuarios y **gRPC** para que los demás MS validen tokens sin acceder a `agm_auth_db`.

## Puertos

| Protocolo | Puerto |
|-----------|--------|
| REST (Gunicorn) | **8001** |
| gRPC | **50051** |

Gateway: `http://localhost:8080/auth/*` y `/usuarios`.

## Variables de entorno

Ver `.env.example`. Críticas:

| Variable | Uso |
|----------|-----|
| `SECRET_KEY` | Firma JWT y validación gRPC |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Vida del access token |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Vida del refresh |
| `INTERNAL_API_KEY` | `POST /usuarios` desde MS-3 (header `X-Internal-Api-Key`) |
| `MS_NOTIFICACIONES_GRPC_*` | Envío de correo reset (MS-6) |
| `FRONTEND_URL` | URL en enlaces de reset |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Seed admin en primer arranque |

## Endpoints REST

| Método | Ruta | Auth |
|--------|------|------|
| POST | `/auth/login` | Público |
| POST | `/auth/refresh-token` | Público |
| GET | `/auth/me` | Bearer JWT |
| POST | `/auth/logout` | Bearer + body `refresh` |
| POST | `/auth/forgot-password` | Público (siempre 200) |
| POST | `/auth/reset-password` | Público |
| GET/POST | `/usuarios` | GET: admin JWT; POST: admin o API key |
| GET/PUT/DELETE | `/usuarios/:id` | Admin |
| POST | `/usuarios/:id/reset-password` | Admin |

Respuestas: envelope `{ success, data, message, errors? }`.

## gRPC (`auth.proto`)

| RPC | Uso |
|-----|-----|
| `ValidateToken` | MS-2…MS-7 en cada request |
| `GetUserById` | Perfil por id |
| `CheckRole` | RBAC fino |
| `CreateUser` | Importaciones MS-3 |

Arranque: `python manage.py grpc_server` (también en `entrypoint.sh`).

## Integración para otros MS

1. Extraer `Authorization: Bearer <token>`.
2. Llamar `ValidateToken` en `ms-auth:50051`.
3. Usar `user_id`, `rol` del response; opcional `CheckRole`.

## Desarrollo

```bash
docker compose up -d ms-auth db-auth
docker exec agm-ms-auth python manage.py test apps.core.tests
./generate_proto.sh   # tras cambiar proto/
```

## Pruebas

Pulido y casos T1–T10: [`docs/RESUMEN_CAMBIOS.md`](../docs/RESUMEN_CAMBIOS.md).  
Postman: carpeta **MS-1 Auth** en `docs/postman/AGM_API_Collection.json`.
