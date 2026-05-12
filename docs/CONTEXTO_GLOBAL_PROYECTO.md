# 🌐 AGM – Contexto Global del Proyecto
> Este documento es el contexto maestro. Cualquier IA que lea esto debe entender la arquitectura completa
> del sistema antes de generar código para cualquier microservicio individual.
>
> **Stack fijo:** Django 5 + DRF en **los 7 MS**, **MySQL 8** (`agm_auth_db`, `agm_periodos_db`, `agm_alumnos_db`, `agm_calificaciones_db`, `agm_asistencias_db`, `agm_notificaciones_db`, `agm_reportes_db`), **Redis** solo en MS-5, **Nginx** como gateway. El backlog (`docs/backlog_AGM_completo.md`) y el enunciado extendido (`docs/Proyecto_Final_SW_AGM.md`) siguen esta línea.

---

## 1. ¿Qué es AGM?

**Sistema de Gestión y Automatización de Calificaciones** para la Facultad de Ciencias de la Computación de la BUAP.
Permite a administradores, docentes y alumnos gestionar periodos académicos, materias, calificaciones,
asistencias por QR, notificaciones por correo y reportes exportables.

---

## 2. Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTE                                  │
│            Angular 20 SPA (Frontend Opcional)                   │
│            o Postman / Swagger UI                               │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP/REST (JSON)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API GATEWAY (Nginx)                           │
│               Punto de entrada único                            │
│     /auth/* → MS-1  |  /periodos/* → MS-2  |  /alumnos/* → MS-3│
│     /calificaciones/* → MS-4  |  /asistencias/* → MS-5         │
│     /notificaciones/* → MS-6  |  /reportes/* → MS-7            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
   │     MS-1      │   │     MS-2      │   │     MS-3      │   ...MS-4…MS-7
   │     Auth      │   │   Periodos    │   │    Alumnos    │
   │    :8001      │   │    :8002      │   │    :8003      │
   │   gRPC:       │   │   gRPC:       │   │   gRPC:       │
   │   50051       │   │   50052       │   │   50053       │
   │    MySQL      │   │    MySQL      │   │    MySQL      │
   │ agm_auth_db   │   │agm_periodos_db│   │ agm_alumnos_db│
   └───────────────┘   └───────────────┘   └───────────────┘
        ▲              ▲              ▲
        └──────gRPC────┴──────gRPC────┘
```

### Reglas de Arquitectura (INVIOLABLES)
1. **Cada MS es un proceso independiente** con su propio puerto REST y gRPC
2. **Cada MS tiene su propia base de datos MySQL** — NUNCA acceder a la BD de otro MS
3. **Comunicación entre MS = gRPC obligatorio** (nunca REST directo entre MS)
4. **Comunicación Cliente → MS = REST/HTTP** (JSON)
5. **Cada MS tiene su propio Dockerfile** y puede desplegarse de forma autónoma
6. **Un solo `docker-compose.yml`** en la raíz levanta todo

---

## 3. Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|-----------|---------|
| **Backend (todos los MS)** | Django REST Framework | Django 5.x + DRF 3.15+ |
| **Base de datos** | MySQL | 8.0 (contenedor Docker) |
| **Comunicación inter-MS** | gRPC + Protocol Buffers | grpcio 1.60+ / proto3 |
| **Cache/Sesiones QR** | Redis | 7.x (solo MS-5) |
| **Frontend (punto extra)** | Angular | 20 |
| **Contenedores** | Docker + Docker Compose | Docker 24+ |
| **Servidor WSGI** | Gunicorn | 21+ |
| **Despliegue cloud** | Railway / Render | — |

---

## 4. Los 7 Microservicios

| MS | Nombre | Puerto REST | Puerto gRPC | Base de Datos | Responsabilidad |
|----|--------|-------------|-------------|---------------|-----------------|
| MS-1 | Auth & Users | 8001 | 50051 | `agm_auth_db` | Login JWT, RBAC, gestión de usuarios |
| MS-2 | Periodos & Materias | 8002 | 50052 | `agm_periodos_db` | CRUD periodos, importación PDF materias |
| MS-3 | Docentes & Alumnos | 8003 | 50053 | `agm_alumnos_db` | Importación PDF docentes, Excel alumnos, bajas. **Cuenta con BD pre-cargada de 43K trabajadores + 318K alumnos BUAP** (ver `test-data/`). Datos con encoding UTF-8 verificado |
| MS-4 | Calificaciones | 8004 | 50054 | `agm_calificaciones_db` | Ponderaciones, actividades, promedios |
| MS-5 | Asistencias QR | 8005 | 50055 | `agm_asistencias_db` + Redis | Sesiones QR, anti-replay, presente/retardo |
| MS-6 | Notificaciones | 8006 | 50056 | `agm_notificaciones_db` | Correos transaccionales (SMTP) |
| MS-7 | Reportes & Stats | 8007 | 50057 | `agm_reportes_db` | Excel/PDF, estadísticas históricas |

---

## 5. Mapa de Comunicación gRPC

Quién llama a quién:

```
MS-2 ──gRPC──► MS-1 (ValidateToken para proteger endpoints)
MS-3 ──gRPC──► MS-1 (ValidateToken + crear usuarios al importar)
MS-3 ──gRPC──► MS-6 (SendBienvenida al importar alumno)
MS-3 ──gRPC──► MS-6 (SendBajaNotif cuando alumno se da de baja)
MS-4 ──gRPC──► MS-1 (ValidateToken)
MS-4 ──gRPC──► MS-3 (GetAlumnosByMateria, IsAlumnoEnMateria)
MS-4 ──gRPC──► MS-2 (GetMateriaById para validar docente)
MS-4 ──gRPC──► MS-6 (SendCierreMateria al cerrar)
MS-5 ──gRPC──► MS-1 (ValidateToken)
MS-5 ──gRPC──► MS-3 (GetAlumnoById, IsAlumnoEnMateria)
MS-6 ──gRPC──► MS-3 (GetAlumnoById para datos del correo)
MS-6 ──gRPC──► MS-2 (GetMateriaById para datos del correo)
MS-7 ──gRPC──► MS-4 (GetConcentrado para reporte calificaciones)
MS-7 ──gRPC──► MS-5 (GetEstadisticasAsistencia para reporte)
MS-7 ──gRPC──► MS-3 (GetAlumnosByMateria para nombres)
MS-7 ──gRPC──► MS-2 (GetMateriasByDocente para historial)
```

---

## 6. Patrones Comunes (TODOS los MS deben seguir esto)

### 6.1 Formato de Respuesta JSON (Estándar)
```json
{
  "success": true,
  "data": { },
  "message": "Operación exitosa",
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100,
    "total_pages": 10
  }
}
```

Respuesta de error:
```json
{
  "success": false,
  "data": null,
  "message": "Descripción del error",
  "errors": {
    "campo": ["detalle del error"]
  }
}
```

### 6.2 Paginación (todos los listados)
- Query params: `?page=1&limit=10`
- Default: page=1, limit=10
- Máximo limit: 100

### 6.3 Autenticación JWT
- Header: `Authorization: Bearer <access_token>`
- Access token expira en 30 minutos
- Refresh token expira en 7 días
- Payload del JWT: `{ user_id, email, rol, nombre }`

### 6.4 Validación de JWT vía gRPC (MS-2 a MS-7)
Cada MS que NO es Auth debe validar el JWT así:
1. Extraer token del header `Authorization: Bearer <token>`
2. Llamar via gRPC a MS-1: `ValidateToken(token)` → recibe `UserClaims`
3. Si es inválido → responder 401
4. Si el rol no tiene permiso → responder 403

### 6.5 Códigos HTTP
| Código | Uso |
|--------|-----|
| 200 | Éxito (GET, PUT) |
| 201 | Recurso creado (POST) |
| 400 | Datos inválidos / regla de negocio violada |
| 401 | No autenticado (JWT inválido o ausente) |
| 403 | Sin permisos (rol incorrecto) |
| 404 | Recurso no encontrado |
| 500 | Error interno del servidor |

### 6.6 Estructura de cada MS Django
```
ms-xxxxx/
├── config/
│   ├── __init__.py
│   ├── settings.py        # Configuración Django (BD, apps, REST, CORS)
│   ├── urls.py             # URLs raíz
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   └── core/               # App principal del MS
│       ├── __init__.py
│       ├── models.py        # Modelos de BD
│       ├── serializers.py   # Serializers DRF
│       ├── views.py         # Vistas/ViewSets
│       ├── urls.py          # URLs de la app
│       ├── permissions.py   # Permisos personalizados
│       ├── pagination.py    # Paginación personalizada
│       └── admin.py
├── grpc_server/             # Servidor gRPC de este MS
│   ├── __init__.py
│   ├── server.py            # Arranque del servidor gRPC
│   └── servicer.py          # Implementación de los métodos gRPC
├── grpc_clients/            # Clientes gRPC hacia otros MS
│   ├── __init__.py
│   ├── auth_client.py       # Cliente hacia MS-1
│   └── ...otros clientes
├── proto/                   # Stubs generados (NO editar manualmente)
│   ├── __init__.py
│   ├── xxxxx_pb2.py
│   └── xxxxx_pb2_grpc.py
├── manage.py
├── requirements.txt
├── Dockerfile
├── .env.example
├── entrypoint.sh            # Script que arranca Gunicorn + gRPC server
└── generate_proto.sh        # Script para regenerar stubs
```

### 6.7 `requirements.txt` base (todos los MS)
```
Django>=5.0,<6.0
djangorestframework>=3.15
django-cors-headers>=4.3
mysqlclient>=2.2
grpcio>=1.60
grpcio-tools>=1.60
python-decouple>=3.8
gunicorn>=21.2
```

### 6.8 `entrypoint.sh` (todos los MS)
```bash
#!/bin/bash
# Esperar a que MySQL esté listo
echo "Esperando a MySQL..."
while ! python -c "import MySQLdb; MySQLdb.connect(host='${DB_HOST}', port=int('${DB_PORT}'), user='${DB_USER}', passwd='${DB_PASSWORD}')" 2>/dev/null; do
  sleep 1
done
echo "MySQL listo!"

# Aplicar migraciones
python manage.py migrate --noinput

# Arrancar servidor gRPC en background
python manage.py grpc_server &

# Arrancar Gunicorn
exec gunicorn config.wsgi:application --bind 0.0.0.0:${REST_PORT} --workers 3
```

### 6.9 Variables de Entorno Comunes
```env
# Django
SECRET_KEY=cambiar-en-produccion
DEBUG=True
ALLOWED_HOSTS=*

# Base de datos MySQL
DB_HOST=db-xxxxx
DB_PORT=3306
DB_NAME=agm_xxxxx_db
DB_USER=root
DB_PASSWORD=root_password
DB_CHARSET=utf8mb4

# Puertos
REST_PORT=800X
GRPC_PORT=5005X

# gRPC de otros MS (solo los que este MS necesita)
MS_AUTH_GRPC_HOST=ms-auth
MS_AUTH_GRPC_PORT=50051
```

### 6.10 Encoding (IMPORTANTE para español)
Las bases de datos contienen nombres con acentos (á, é, í, ó, ú), ñ y ü.
Todos los MS deben usar `utf8mb4` para evitar corrupción de caracteres.

**En `settings.py`:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', cast=int),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
```

**En Docker:** Los contenedores MySQL ya están configurados con:
```yaml
command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
```

**Al importar seeds SQL:**
```bash
mysql -u root -proot_password --default-character-set=utf8mb4 agm_alumnos_db < seed_docentes_mysql.sql
```

---

## 7. Roles del Sistema

| Rol | Puede hacer |
|-----|------------|
| **admin** | Todo: gestionar periodos, importar PDF/Excel, gestionar docentes/usuarios |
| **docente** | Gestionar sus materias, calificaciones, pase de lista QR, exportar reportes |
| **alumno** | Consultar calificaciones, generar QR para asistencia, solicitar baja |

---

## 8. Despliegue

### Local (Desarrollo)

El archivo `docker-compose.yml` en la raíz define **siete servicios MySQL 8** (`db-auth` … `db-reportes`, bases `agm_*_db`), **Redis** para MS-5 y los **siete microservicios** con `depends_on` + `healthcheck` en las BDs.

**Dentro de la red Docker:** en cada `.env`, `DB_HOST` debe ser el **nombre del servicio** de MySQL (p. ej. `db-auth`), `DB_PORT=3306`. Para depurar desde el **host** con un cliente MySQL, los puertos publicados van del **13307 al 13313** (mapeo a `3306` en el contenedor; ver `docker-compose.yml`), así se evita chocar con otros MySQL típicos en 3307.

**API Gateway Nginx:** servicio `nginx` en el compose, **http://localhost:8080** → enrutamiento a cada MS según prefijo (`docker/nginx/default.conf`). Los REST también siguen en **8001–8007**; **gRPC** entre MS en **50051–50057** (red interna, sin pasar por Nginx).

```bash
# Clonar repo
git clone https://github.com/Guillermo1804/proyecto_final_servicios.git
cd proyecto_final_servicios

# Copiar .env.example a .env en cada MS y completar variables

# Levantar todo (Compose V2 recomendado)
docker compose up --build
# o: docker-compose up --build
```

### Producción (Railway/Render)
Cada MS se despliega como un servicio independiente:
- Railway soporta Docker nativo + MySQL gestionado
- Cada MS tiene su propia URL pública con HTTPS automático
- Variables de entorno se configuran en el dashboard de la plataforma (NUNCA en el repo)

**¿Qué es Railway?** Es una plataforma en la nube (como Heroku) donde subes tu código/Docker y
te da una URL pública con HTTPS para que cualquier persona en internet pueda acceder a tu API.
Es gratis con límites. Alternativas: Render, Fly.io, AWS, Google Cloud.

---

## 9. Criterios de Evaluación (Resumen)

| Criterio | Peso | Lo que más importa |
|----------|------|-------------------|
| Arquitectura MS real | 30% | Procesos separados, BDs propias, Dockerfiles individuales |
| gRPC entre servicios | 20% | .proto correctos, al menos 3 pares comunicándose |
| Funcionalidad backend | 25% | Todos los módulos operativos end-to-end |
| Despliegue producción | 10% | URLs públicas HTTPS funcionando |
| Calidad código/repo | 8% | +20 commits, .env.example, estructura limpia |
| Documentación | 7% | Manual Técnico, Manual Usuario, README, Postman |
| **Frontend Angular** | **+1 punto extra** | Solo si está 100% completo y conectado |

### Penalizaciones graves
- Monolito disfrazado: **−20 puntos**
- Sin gRPC (usar REST entre MS): **−15 puntos**
- Sin despliegue: **−10 puntos**
- Repo con <20 commits: **−10 puntos**
- Módulo no funcional: **−5 por módulo**
