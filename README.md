# AGM — Sistema de Gestión Académica FCC BUAP

Sistema distribuido de 7 microservicios Django/DRF para la gestión integral del ciclo académico: periodos, materias, docentes, alumnos, calificaciones, asistencia por código QR, notificaciones por correo electrónico y reportes estadísticos.  
Desarrollado como proyecto final de la materia **Servicios Web** — Facultad de Ciencias de la Computación, BUAP.

---

## 👥 Integrantes y Responsabilidades

| Integrante | Microservicios Asignados | Epics |
|---|---|---|
| **Alan** | MS-2 Periodos & Materias · MS-3 Docentes & Alumnos · Documentación | Epic 4, Epic 5, Epic 11 |
| **Gerardo** | MS-1 Auth & Users · Frontend Angular | Epic 3, Epic 10 |
| **Guillermo** | MS-4 Calificaciones · MS-5 Asistencias QR · Arquitectura gRPC | Epic 2, Epic 6, Epic 7 |
| **Hector** | MS-6 Notificaciones · MS-7 Reportes · Infraestructura | Epic 1, Epic 8, Epic 9 |

---

## 🏗️ Arquitectura

```
Cliente (Angular 20 / Postman)
        │
        │ HTTP/JSON
        ▼
   Nginx :8080  ── gateway único
        │
   ┌────┴────┬────┬────┬────┬────┬────┬────┐
   │ MS-1    │MS-2│MS-3│MS-4│MS-5│MS-6│MS-7│
   │ :8001   │8002│8003│8004│8005│8006│8007│
   └────┬────┴────┴────┴────┴────┴────┴────┘
        │         │
        │    RabbitMQ (agm.domain)
        │    Outbox / Inbox por MS
        ▼
   JWKS (validación JWT local)
```

| MS | Servicio | Puerto REST | Base de Datos |
|---|---|---|---|
| MS-1 | Auth & Users | 8001 | agm_auth_db |
| MS-2 | Periodos & Materias | 8002 | agm_periodos_db |
| MS-3 | Docentes & Alumnos | 8003 | agm_alumnos_db |
| MS-4 | Calificaciones & Ponderaciones | 8004 | agm_calificaciones_db |
| MS-5 | Asistencias QR | 8005 | agm_asistencias_db + Redis |
| MS-6 | Notificaciones (correos) | 8006 | agm_notificaciones_db |
| MS-7 | Reportes & Estadísticas | 8007 | agm_reportes_db |

---

## 📋 Requisitos

| Software | Versión mínima |
|---|---|
| **Docker Desktop** | ≥ 24.x |
| **Docker Compose** | ≥ 2.x (plugin V2) |
| Git | ≥ 2.40 |

> No se requiere instalar Python, Node.js, MySQL ni Redis en el host. Todo corre dentro de contenedores Docker.

---

## 🚀 Instalación y Ejecución Local

### 1. Clonar el repositorio

```bash
git clone https://github.com/Guillermo1804/proyecto_final_servicios.git
cd proyecto_final_servicios
```

### 2. Configurar variables de entorno

```bash
# Copiar el .env raíz
cp .env.example .env

# Copiar el .env de cada microservicio
for ms in ms-auth ms-periodos ms-alumnos ms-calificaciones ms-asistencias ms-notificaciones ms-reportes; do
  cp $ms/.env.example $ms/.env
done
```

### 3. Generar código protobuf (gRPC)

```bash
# Desde la raíz del proyecto
chmod +x proto/generate_proto.sh
./proto/generate_proto.sh
```

### 4. Levantar el stack completo

```bash
docker compose up --build
```

Esto levanta **25+ contenedores**: 7 microservicios, 7 bases de datos MySQL, RabbitMQ, Redis, Nginx (gateway), 5 outbox workers y 7 consumer workers.

### 5. Verificar que los servicios estén activos

```bash
# Health check por servicio
curl http://localhost:8080/ms-auth/health/
curl http://localhost:8080/ms-periodos/health/
curl http://localhost:8080/ms-alumnos/health/
# ... o directamente:
curl http://localhost:8001/health/
curl http://localhost:8002/health/
curl http://localhost:8003/health/
```

### Accesos locales

| Recurso | URL |
|---|---|
| **Gateway Nginx** | http://localhost:8080 |
| MS-1 Auth (directo) | http://localhost:8001 |
| MS-2 Periodos (directo) | http://localhost:8002 |
| MS-3 Alumnos (directo) | http://localhost:8003 |
| MS-4 Calificaciones (directo) | http://localhost:8004 |
| MS-5 Asistencias (directo) | http://localhost:8005 |
| MS-6 Notificaciones (directo) | http://localhost:8006 |
| MS-7 Reportes (directo) | http://localhost:8007 |
| RabbitMQ Management | http://localhost:15672 (guest/guest) |
| MySQL en host | Puertos 13307–13313 (root/root_password) |

---

## 🌐 URLs de Producción

| Servicio | URL |
|---|---|
| Gateway API | https://agm.iokoia.com/api/ |
| Frontend Angular | https://agm.iokoia.com/ |

---

## ✅ Estado de Tests

| Microservicio | Tests | Estado |
|---|---|---|
| MS-2 (Periodos & Materias) | **13 passed** · 0 failed | ✅ |
| MS-3 (Docentes & Alumnos) | **24 passed** · 0 failed | ✅ |
| MS-6 (Notificaciones) | **20 passed** · 0 failed | ✅ |
| MS-7 (Reportes) | **34 passed** · 0 failed | ✅ |

Ejecutar tests dentro de los contenedores:

```bash
docker exec agm-ms-periodos python manage.py test apps.core
docker exec agm-ms-alumnos python manage.py test apps.core
docker exec agm-ms-notificaciones python manage.py test
docker exec agm-ms-reportes python manage.py test
```

---

## 📂 Estructura del Repositorio

```
proyecto_final_servicios/
├── ms-auth/                  # MS-1: Autenticación JWT, CRUD usuarios
├── ms-periodos/              # MS-2: Periodos académicos, catálogo de materias
├── ms-alumnos/               # MS-3: Docentes, alumnos, inscripciones
├── ms-calificaciones/        # MS-4: Ponderaciones, actividades, calificaciones
├── ms-asistencias/           # MS-5: Sesiones QR, registro de asistencia
├── ms-notificaciones/        # MS-6: Correos transaccionales
├── ms-reportes/              # MS-7: Reportes PDF/XLSX, estadísticas
├── frontend/                 # Angular 20 + Angular Material
├── proto/                    # Archivos .proto (definiciones gRPC)
├── packages/agm_events/      # Librería compartida del bus de eventos
├── contracts/events/          # Catálogo de eventos RabbitMQ
├── docker/nginx/              # Configuración del gateway Nginx
├── docs/                     # Documentación técnica
│   ├── manual_tecnico.md     # Manual técnico completo
│   ├── GUIA_INTEGRACION_MS2_MS3.md  # Guía de integración frontend
│   ├── CONTEXTO_GLOBAL_PROYECTO.md  # Arquitectura y reglas
│   └── microservicios/       # Specs individuales por MS
├── test-data/                # Seeds: PDFs y datos de prueba BUAP
├── docker-compose.yml        # Stack completo (25+ contenedores)
├── Deuda_Tecnica.md          # Registro de deuda técnica y sprints
└── README.md                 # Este archivo
```

---

## 📖 Documentación Adicional

| Documento | Descripción |
|---|---|
| [Manual Técnico](docs/manual_tecnico.md) | Arquitectura, modelos, endpoints de los 7 MS |


---

## ⚙️ Stack Tecnológico

- **Backend:** Django 5 · Django REST Framework 3.15 · simplejwt 5.3
- **Base de Datos:** MySQL 8 (utf8mb4) — una BD aislada por microservicio
- **Mensajería:** RabbitMQ (patrón Outbox/Inbox transaccional)
- **Caché:** Redis 7 (sesiones QR en MS-5)
- **gRPC:** grpcio 1.60+ (comunicación inter-MS legacy / admin)
- **PDF:** pdfplumber 0.10+ (import) · reportlab 4.1+ (export)
- **Excel:** openpyxl 3.1+ · pandas 2.2+
- **Frontend:** Angular 20 (standalone signals) · Angular Material 20 · Bootstrap Icons 1.13
- **Gateway:** Nginx 1.25 (puerto 8080)
- **Despliegue:** Docker Compose (local) · Railway (producción)
