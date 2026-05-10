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
| **[Nombre 1]** | Líder / Arquitecto / DevOps | Infraestructura + MS-1 Auth | correo@buap.mx |
| **[Nombre 2]** | Desarrollador Backend | MS-2 Periodos + MS-3 Alumnos | correo@buap.mx |
| **[Nombre 3]** | Desarrollador Backend | MS-4 Calificaciones + MS-5 Asistencias QR | correo@buap.mx |
| **[Nombre 4]** | Desarrollador Backend + QA | MS-6 Notificaciones + MS-7 Reportes + Docs | correo@buap.mx |

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
agm-backend/
├── ms-auth/                 # MS-1: Autenticación JWT y gestión de usuarios
├── ms-periodos/             # MS-2: Periodos académicos e importación de materias
├── ms-alumnos/              # MS-3: Docentes, alumnos e inscripciones
├── ms-calificaciones/       # MS-4: Ponderaciones, actividades y calificaciones
├── ms-asistencias/          # MS-5: Sesiones QR y registro de asistencia
├── ms-notificaciones/       # MS-6: Correos transaccionales
├── ms-reportes/             # MS-7: Reportes Excel/PDF y estadísticas
├── proto/                   # Archivos .proto compartidos (contratos gRPC)
├── frontend/                # Angular 20 SPA (punto extra)
├── docs/                    # Documentación del proyecto
├── docker-compose.yml       # Levanta todo el sistema con un comando
├── .gitignore
└── README.md
```

---

## 🚀 Instalación Local

### Prerrequisitos
- Docker 24+ y Docker Compose v2+
- Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/EQUIPO/agm-backend.git
cd agm-backend

# 2. Copiar .env.example a .env en cada microservicio
for dir in ms-auth ms-periodos ms-alumnos ms-calificaciones ms-asistencias ms-notificaciones ms-reportes; do
  cp $dir/.env.example $dir/.env
done

# 3. Completar las variables de entorno en cada .env

# 4. Levantar todo el sistema
docker-compose up --build

# 5. Acceder a los servicios:
# MS-1 Auth:           http://localhost:8001
# MS-2 Periodos:       http://localhost:8002
# MS-3 Alumnos:        http://localhost:8003
# MS-4 Calificaciones: http://localhost:8004
# MS-5 Asistencias:    http://localhost:8005
# MS-6 Notificaciones: http://localhost:8006
# MS-7 Reportes:       http://localhost:8007
```

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
