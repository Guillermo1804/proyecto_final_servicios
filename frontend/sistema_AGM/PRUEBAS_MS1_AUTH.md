# Pruebas frontend — MS-1 Auth (primera integracion)

## Requisitos previos

1. Backend (minimo para login):

```bash
docker compose up -d rabbitmq db-auth ms-auth nginx
```

2. Frontend:

```bash
cd frontend/sistema_AGM
npm install
npm start
```

Abre: http://localhost:4200

API gateway: http://127.0.0.1:8080 (el front en dev usa `proxy.conf.json` hacia ese puerto)

## Datos visibles en UI (MS-1)

Tras login, en **todas** las pantallas con barra superior:

- Nombre real del usuario (`GET /auth/me` + login)
- Rol: Administrador / Docente / Alumno
- Correo

Dashboards ya no muestran nombres inventados (ej. "Dr. Silva"); la fecha del docente es la de hoy.

## Credenciales de prueba

| Rol | Email | Password |
|-----|-------|----------|
| Admin | admin@agm.buap.mx | admin123 |

(Usa docente/alumno si existen en tu BD de MS-1.)

## Casos que deben probar los testers

### 1. Login exitoso (admin)

1. Ir a `/login`
2. Email: `admin@agm.buap.mx`, password: `admin123`
3. Clic en iniciar sesion
4. Debe redirigir a `/admin/dashboard`
5. En DevTools > Application > Session Storage: claves `agm_access_token`, `agm_refresh_token`, `agm_user_role`

### 2. Login fallido

1. Password incorrecta
2. Mensaje: "Credenciales invalidas" (401)

### 3. Rutas protegidas

1. Sin login, abrir `http://localhost:4200/admin/dashboard`
2. Debe mandar a `/login`
3. Tras login admin, debe entrar al dashboard

### 4. Cerrar sesion

1. En topbar admin, boton cerrar sesion
2. Vuelve a `/login`
3. Tokens borrados del storage

### 5. Olvide mi contraseña

1. `/forgot-password` — ingresar email
2. Mensaje generico de exito (aunque el correo no exista)
3. Requiere MS-6 + worker si quieres correo real

### 6. Refresh token (opcional tecnico)

1. Login
2. Esperar o forzar 401 en otra llamada
3. El interceptor debe llamar `POST /auth/refresh-token` y reintentar

## Endpoints MS-1 usados por el frontend

| Accion | Metodo | URL |
|--------|--------|-----|
| Login | POST | `/auth/login` |
| Refresh | POST | `/auth/refresh-token` body `{ "refresh": "..." }` |
| Perfil | GET | `/auth/me` |
| Logout | POST | `/auth/logout` body `{ "refresh": "..." }` |
| Olvidar password | POST | `/auth/forgot-password` |
| Reset password | POST | `/auth/reset-password` |

## Problemas comunes

| Sintoma | Solucion |
|---------|----------|
| Error de conexion (status 0) | Levantar `nginx` y `ms-auth` |
| 404 en login | Verificar `environment.apiBaseUrl` = `http://127.0.0.1:8080` |
| Entra a login pero no redirige | Revisar que la respuesta traiga `success: true` y `data.access_token` |
