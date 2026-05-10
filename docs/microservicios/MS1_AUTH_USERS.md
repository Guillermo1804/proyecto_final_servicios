# 🔐 MS-1: Auth & Users — Especificación Completa para IA

> **Lee primero**: `docs/CONTEXTO_GLOBAL_PROYECTO.md` para entender la arquitectura general.

---

## Identidad del Microservicio

| Campo | Valor |
|-------|-------|
| **Nombre** | ms-auth |
| **Carpeta** | `/ms-auth/` |
| **Puerto REST** | 8001 |
| **Puerto gRPC** | 50051 |
| **Base de datos** | MySQL – `agm_auth_db` |
| **Responsabilidad** | Autenticación JWT, gestión de credenciales, RBAC, recuperación de contraseña. Centraliza la identidad de TODOS los usuarios del sistema |

---

## Dependencias Python (`requirements.txt`)

```
Django>=5.0,<6.0
djangorestframework>=3.15
djangorestframework-simplejwt>=5.3
django-cors-headers>=4.3
mysqlclient>=2.2
grpcio>=1.60
grpcio-tools>=1.60
python-decouple>=3.8
gunicorn>=21.2
```

---

## Modelos de Base de Datos

### `User` (modelo personalizado, hereda de `AbstractBaseUser`)
```python
class User(AbstractBaseUser, PermissionsMixin):
    email = EmailField(unique=True, max_length=255)          # Login con email
    nombre = CharField(max_length=255)
    rol = CharField(max_length=20, choices=[
        ('admin', 'Administrador'),
        ('docente', 'Docente'),
        ('alumno', 'Alumno'),
    ])
    activo = BooleanField(default=True)
    fecha_creacion = DateTimeField(auto_now_add=True)
    fecha_actualizacion = DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'rol']
```

### `PasswordResetToken`
```python
class PasswordResetToken(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    token = UUIDField(default=uuid4, unique=True)
    expira_en = DateTimeField()            # Ahora + 1 hora al crear
    usado = BooleanField(default=False)
    creado_en = DateTimeField(auto_now_add=True)
```

---

## Endpoints REST

### Autenticación (Públicos)

#### `POST /auth/login`
- **Auth requerida**: No
- **Body**:
  ```json
  { "email": "docente@correo.buap.mx", "password": "clave123" }
  ```
- **Response 200**:
  ```json
  {
    "success": true,
    "data": {
      "access_token": "eyJ...",
      "refresh_token": "eyJ...",
      "user": { "id": 1, "email": "...", "nombre": "...", "rol": "docente" }
    },
    "message": "Login exitoso"
  }
  ```
- **Response 401**: Credenciales incorrectas o usuario inactivo

#### `POST /auth/refresh-token`
- **Auth requerida**: No
- **Body**: `{ "refresh_token": "eyJ..." }`
- **Response 200**: `{ "access_token": "nuevo_eyJ..." }`
- **Response 401**: Refresh token inválido o expirado

#### `POST /auth/forgot-password`
- **Auth requerida**: No
- **Body**: `{ "email": "usuario@correo.buap.mx" }`
- **Lógica**:
  1. Buscar usuario por email
  2. Generar `PasswordResetToken` con expiración de 1 hora
  3. Llamar via gRPC a MS-6: `SendResetPassword(email, token)`
  4. Siempre retornar 200 (no revelar si el email existe o no)
- **Response 200**: `{ "message": "Si el correo existe, se envió un enlace de recuperación" }`

#### `POST /auth/reset-password`
- **Auth requerida**: No
- **Body**: `{ "token": "uuid-del-token", "nueva_password": "nuevaClave123" }`
- **Lógica**:
  1. Buscar token en BD
  2. Verificar que no haya expirado y no haya sido usado
  3. Actualizar contraseña del usuario
  4. Marcar token como `usado = True`
- **Response 200**: `{ "message": "Contraseña actualizada exitosamente" }`
- **Response 400**: Token inválido, expirado o ya usado

### Autenticación (Protegidos)

#### `GET /auth/me`
- **Auth**: JWT requerido (cualquier rol)
- **Response 200**:
  ```json
  {
    "success": true,
    "data": { "id": 1, "email": "...", "nombre": "...", "rol": "docente" }
  }
  ```

#### `POST /auth/logout`
- **Auth**: JWT requerido
- **Body**: `{ "refresh_token": "eyJ..." }`
- **Lógica**: Agregar refresh token a blacklist (simplejwt)
- **Response 200**: `{ "message": "Sesión cerrada" }`

### Gestión de Usuarios (Solo Admin)

#### `GET /usuarios`
- **Auth**: JWT + rol `admin`
- **Query params**: `?page=1&limit=10&search=nombre_o_email&rol=docente`
- **Response 200**: Lista paginada de usuarios

#### `GET /usuarios/:id`
- **Auth**: JWT + rol `admin`
- **Response 200**: Datos completos del usuario

#### `POST /usuarios`
- **Auth**: JWT admin O API key interna (para que MS-3 cree usuarios al importar)
- **Body**:
  ```json
  {
    "email": "alumno@correo.buap.mx",
    "nombre": "Juan Pérez",
    "rol": "alumno",
    "password": "clave_generada_uuid"
  }
  ```
- **Response 201**: `{ "data": { "id": 5, "email": "...", ... } }`
- **Response 400**: Email ya existe

#### `PUT /usuarios/:id`
- **Auth**: JWT + rol `admin`
- **Body**: `{ "nombre": "...", "activo": true }`
- **Response 200**: Usuario actualizado

#### `POST /usuarios/:id/reset-password`
- **Auth**: JWT + rol `admin`
- **Lógica**: Genera nueva contraseña temporal, la asigna al usuario
- **Response 200**: `{ "data": { "nueva_password": "temp_uuid" } }`

#### `DELETE /usuarios/:id`
- **Auth**: JWT + rol `admin`
- **Lógica**: Soft delete → `activo = False`
- **Response 200**: `{ "message": "Usuario desactivado" }`

---

## Servidor gRPC (Puerto 50051)

Este MS **expone** estos métodos gRPC para que los demás MS lo llamen:

### Archivo proto: `/proto/auth.proto`
```protobuf
syntax = "proto3";
package auth;

service AuthService {
  rpc ValidateToken(ValidateTokenRequest) returns (ValidateTokenResponse);
  rpc GetUserById(GetUserByIdRequest) returns (UserProfile);
  rpc CheckRole(CheckRoleRequest) returns (CheckRoleResponse);
  rpc CreateUser(CreateUserRequest) returns (CreateUserResponse);
}

message ValidateTokenRequest {
  string token = 1;
}

message ValidateTokenResponse {
  bool valid = 1;
  int32 user_id = 2;
  string email = 3;
  string nombre = 4;
  string rol = 5;
}

message GetUserByIdRequest {
  int32 user_id = 1;
}

message UserProfile {
  int32 id = 1;
  string email = 2;
  string nombre = 3;
  string rol = 4;
  bool activo = 5;
}

message CheckRoleRequest {
  int32 user_id = 1;
  string role = 2;
}

message CheckRoleResponse {
  bool has_role = 1;
}

message CreateUserRequest {
  string email = 1;
  string nombre = 2;
  string rol = 3;
  string password = 4;
}

message CreateUserResponse {
  bool success = 1;
  int32 user_id = 2;
  string message = 3;
}
```

### Implementación del Servicer
- `ValidateToken`: Decodifica el JWT con la misma `SECRET_KEY`, retorna claims si es válido
- `GetUserById`: Consulta la BD y retorna el perfil
- `CheckRole`: Consulta la BD y verifica si `user.rol == role`
- `CreateUser`: Crea usuario en la BD (usado por MS-3 al importar alumnos/docentes)

---

## Clientes gRPC (este MS llama a)

| MS destino | Método | Cuándo |
|-----------|--------|--------|
| MS-6 Notificaciones | `SendResetPassword` | Cuando se solicita recuperación de contraseña |

---

## Variables de Entorno (`.env.example`)

```env
SECRET_KEY=django-insecure-cambiar-en-produccion
DEBUG=True
ALLOWED_HOSTS=*

DB_HOST=db-auth
DB_PORT=3306
DB_NAME=agm_auth_db
DB_USER=root
DB_PASSWORD=root_password

REST_PORT=8001
GRPC_PORT=50051

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=30
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# gRPC hacia otros MS
MS_NOTIFICACIONES_GRPC_HOST=ms-notificaciones
MS_NOTIFICACIONES_GRPC_PORT=50056
```

---

## Configuración especial de Django (`settings.py`)

```python
AUTH_USER_MODEL = 'core.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardPagination',
    'PAGE_SIZE': 10,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'TOKEN_OBTAIN_SERIALIZER': 'apps.core.serializers.CustomTokenObtainPairSerializer',
}
```

---

## Reglas de Negocio Críticas

1. El login es por **email + password** (NO por username)
2. El JWT debe incluir en el payload: `user_id`, `email`, `rol`, `nombre`
3. Los access tokens expiran en 30 minutos
4. Los refresh tokens expiran en 7 días y se rotan (blacklist el anterior)
5. La recuperación de contraseña genera un token UUID de un solo uso que expira en 1 hora
6. Al crear un alumno, MS-3 llama a este MS via gRPC `CreateUser` para generar el usuario
7. El Admin puede forzar reset de contraseña de cualquier usuario
8. Soft delete: nunca borrar usuarios, solo marcar `activo = False`
9. **SIEMPRE** retornar 200 en `forgot-password` aunque el email no exista (seguridad)

---

## Notas para la IA

- Este es el MS más crítico: si Auth no funciona, NADA funciona
- Usar `djangorestframework-simplejwt` con blacklist habilitado
- El servidor gRPC debe correr en un hilo/proceso separado junto con Gunicorn
- El `CreateUser` gRPC es esencial para que MS-3 pueda importar alumnos y docentes
- Crear un superusuario admin por defecto en las migraciones iniciales o en un management command
