# 🎓 AGM — Sistema de Gestión y Automatización de Calificaciones

**Proyecto Final – Servicios Web**
Facultad de Ciencias de la Computación | Benemérita Universidad Autónoma de Puebla

---

## 📋 Descripción

AGM es una plataforma académica digital que permite a la Facultad de Ciencias de la Computación de la BUAP gestionar integralmente sus procesos académicos: periodos, materias, docentes, alumnos, calificaciones, asistencias por código QR, notificaciones por correo electrónico y reportes exportables. El sistema está construido sobre una arquitectura de **7 microservicios independientes** comunicados mediante **gRPC**, cada uno con su propia base de datos.

---

## 👥 Equipo e Integrantes

| Nombre | Rol | Microservicios | Contacto |
|--------|-----|----------------|----------|
| **[Persona 1]** | Líder / Arquitecto / DevOps | Infraestructura + MS-1 Auth | _(completar)_ |
| **[Persona 2]** | Desarrollador Backend | MS-2 Periodos + MS-3 Alumnos | _(completar)_ |
| **[Persona 3]** | Desarrollador Backend | MS-4 Calificaciones + MS-5 Asistencias QR | _(completar)_ |
| **[Persona 4]** | Desarrollador Backend + QA | MS-6 Notificaciones + MS-7 Reportes + Docs | _(completar)_ |

> ⚠️ **TODO**: Completar nombres reales y correos del equipo

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| Backend (7 MS) | Django 5.x + Django REST Framework |
| Base de datos | MySQL 8.0 (una instancia por MS) |
| Comunicación inter-MS | gRPC + Protocol Buffers (proto3) |
| Cache/Sesiones QR | Redis 7.x |
| Frontend | Angular 20 |
| Contenedores | Docker + Docker Compose |
| Servidor WSGI | Gunicorn |
| Despliegue | Railway |

---

## 🏗️ Arquitectura de Microservicios

| MS | Nombre | Puerto REST | Puerto gRPC | Base de Datos |
|----|--------|-------------|-------------|---------------|
| MS-1 | Auth & Users | 8001 | 50051 | agm_auth_db |
| MS-2 | Periodos & Materias | 8002 | 50052 | agm_periodos_db |
| MS-3 | Docentes & Alumnos | 8003 | 50053 | agm_alumnos_db |
| MS-4 | Calificaciones & Ponderaciones | 8004 | 50054 | agm_calificaciones_db |
| MS-5 | Asistencias QR | 8005 | 50055 | agm_asistencias_db |
| MS-6 | Notificaciones | 8006 | 50056 | agm_notificaciones_db |
| MS-7 | Reportes & Estadísticas | 8007 | 50057 | agm_reportes_db |

---

## 📁 Estructura del Repositorio

```
proyecto_final_servicios/
├── ms-auth/
├── ms-periodos/
├── ms-alumnos/
├── ms-calificaciones/
├── ms-asistencias/
├── ms-notificaciones/
├── ms-reportes/
├── proto/
├── frontend/
├── docker/
│   └── nginx/
│       └── default.conf      # API Gateway: prefijos → microservicios
├── docs/
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 🚀 Instalación Local (Docker)

### Prerrequisitos
- Docker 24+ con el plugin **Docker Compose V2** (`docker compose version`)
- Git
- En cada carpeta `ms-*` debe existir un **`Dockerfile`** (el repositorio ya incluye uno por microservicio) y **`entrypoint.sh`**. Si falta algún archivo, `docker compose build` fallará.

### Variables y red Docker
- Compose exige el archivo **`ms-*/.env`** (no solo `.env.example`). Cópialo antes de levantar los contenedores.
- Dentro de la red `agm-network`, cada microservicio debe usar como **`DB_HOST`** el nombre del servicio de base de datos (por ejemplo `db-auth` para MS-1), **`DB_PORT=3306`** y las credenciales alineadas con `docker-compose.yml` (`DB_USER` / `DB_PASSWORD` como en tu `.env.example`).
- Los hosts de gRPC hacia otros MS deben ser los **nombres de servicio** (`ms-auth`, `ms-periodos`, etc.), no `localhost`.
- **Redis** (MS-5): servicio `redis`, puerto interno `6379`; revisa `ms-asistencias/.env.example` para la URL o host/puerto que use el proyecto.

### Puertos MySQL publicados en el host (opcional)
Solo si conectas un cliente MySQL **desde tu máquina** a las BDs: el puerto **dentro** de Docker sigue siendo 3306; en el host están mapeados así:

| Servicio Compose | Base de datos       | URL típica desde el host   |
|------------------|---------------------|-----------------------------|
| `db-auth`        | `agm_auth_db`       | `127.0.0.1:13307` (→3306)  |
| `db-periodos`    | `agm_periodos_db`   | `127.0.0.1:13308`          |
| `db-alumnos`     | `agm_alumnos_db`    | `127.0.0.1:13309`          |
| `db-calificaciones` | `agm_calificaciones_db` | `127.0.0.1:13310`     |
| `db-asistencias` | `agm_asistencias_db`| `127.0.0.1:13311`          |
| `db-notificaciones` | `agm_notificaciones_db` | `127.0.0.1:13312`     |
| `db-reportes`    | `agm_reportes_db`   | `127.0.0.1:13313`          |

### Pasos

**Bash (Linux / macOS / Git Bash)**

```bash
# 1. Clonar el repositorio
git clone https://github.com/Guillermo1804/proyecto_final_servicios.git
cd proyecto_final_servicios

# 2. Copiar .env.example a .env en cada microservicio
for dir in ms-auth ms-periodos ms-alumnos ms-calificaciones ms-asistencias ms-notificaciones ms-reportes; do
  cp "$dir/.env.example" "$dir/.env"
done

# 3. Revisar / completar variables en cada .env (JWT, SMTP, hosts gRPC, etc.)

# 4. Levantar todo (Compose V2)
docker compose up --build
# equivalente legacy: docker-compose up --build
```

**PowerShell (Windows)**

```powershell
foreach ($d in 'ms-auth','ms-periodos','ms-alumnos','ms-calificaciones','ms-asistencias','ms-notificaciones','ms-reportes') {
  Copy-Item "$d\.env.example" "$d\.env"
}
docker compose up --build
```

### Arranque y dependencias entre MS
`depends_on` garantiza que cada MS espere **su** MySQL (y MS-5 además a Redis). **No** ordena el arranque entre microservicios que se llaman por gRPC: si un servicio falla al inicio porque otro aún no escucha en gRPC, suele bastar un reinicio del contenedor afectado o añadir reintentos en el cliente gRPC (recomendado en producción).

### API Gateway (Nginx)
Tras `docker compose up`, el **punto de entrada único** para REST es **http://localhost:8080** (servicio `nginx`, mapeo `8080:80`). La configuración vive en `docker/nginx/default.conf` (prefijos `/auth/`, `/periodos/`, `/materias/`, `/docentes/`, `/alumnos/`, rutas de calificaciones, asistencias, notificaciones y reportes).

Los microservicios siguen publicados **directamente** en **8001–8007** para depuración, **Django Admin** (`/admin/`) y herramientas que apunten a un puerto concreto. **gRPC** (50051–50057) solo entre contenedores; no pasa por Nginx.

### URLs locales tras `docker compose up`

| Entrada | URL |
|--------|-----|
| **API Gateway (Nginx)** | http://localhost:8080 |
| MS-1 Auth | http://localhost:8001 |
| MS-2 Periodos | http://localhost:8002 |
| MS-3 Alumnos | http://localhost:8003 |
| MS-4 Calificaciones | http://localhost:8004 |
| MS-5 Asistencias | http://localhost:8005 |
| MS-6 Notificaciones | http://localhost:8006 |
| MS-7 Reportes | http://localhost:8007 |

Django Admin en cada MS: `http://localhost:800X/admin/` (no enrutado por el gateway).

---

## 🌐 URLs de Producción

| Microservicio | URL |
|--------------|-----|
| MS-1 Auth | `https://agm-auth.up.railway.app` |
| MS-2 Periodos | `https://agm-periodos.up.railway.app` |
| MS-3 Alumnos | `https://agm-alumnos.up.railway.app` |
| MS-4 Calificaciones | `https://agm-calificaciones.up.railway.app` |
| MS-5 Asistencias | `https://agm-asistencias.up.railway.app` |
| MS-6 Notificaciones | `https://agm-notificaciones.up.railway.app` |
| MS-7 Reportes | `https://agm-reportes.up.railway.app` |
| Frontend | `https://agm-frontend.vercel.app` |

> ⚠️ Las URLs se actualizarán al realizar el despliegue.

---

## 🎬 Video Demostrativo

📹 [Ver video en YouTube](https://youtube.com/watch?v=PENDIENTE)

---

## 📚 Documentación

- [Manual Técnico](docs/manual_tecnico.pdf)
- [Manual de Usuario](docs/manual_usuario.pdf)
- [Colección Postman](docs/postman_collection.json)
- [Contratos gRPC (.proto)](proto/)

---

## 📄 Licencia

Proyecto académico — BUAP FCC — Servicios Web 2026
