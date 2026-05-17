# 📋 Backlog Completo de Issues – Sistema AGM (Academic Grade Management)
> Proyecto Final – Servicios Web | BUAP – FCC
> Stack: **Django 5 + DRF en los 7 MS** · **MySQL 8** (una BD por MS; Redis solo en `ms-asistencias`) · gRPC · Docker · Angular 20 (Frontend – Punto Extra)
>
> **Alineación:** Este backlog sigue `docs/CONTEXTO_GLOBAL_PROYECTO.md` (sin mezcla de motores ni frameworks por microservicio).

---

## 🗂️ ÍNDICE DE EPICS

| Epic | Nombre | Issues |
|------|--------|--------|
| Epic 1 | Infraestructura y DevOps | ISSUE-101 al 107 |
| Epic 2 | Arquitectura y Comunicación gRPC | ISSUE-201 al 204 |
| Epic 3 | ms-auth: Auth & Users | ISSUE-301 al 308 |
| Epic 4 | ms-periodos: Periodos & Materias | ISSUE-401 al 408 |
| Epic 5 | ms-alumnos: Docentes & Alumnos | ISSUE-501 al 509 |
| Epic 6 | ms-calificaciones: Calificaciones & Ponderaciones | ISSUE-601 al 609 |
| Epic 7 | ms-asistencias: Asistencias QR | ISSUE-701 al 708 |
| Epic 8 | ms-notificaciones: Notificaciones | ISSUE-801 al 806 |
| Epic 9 | ms-reportes: Reportes & Estadísticas | ISSUE-901 al 907 |
| Epic 10 | Frontend Angular 20 (Punto Extra) | ISSUE-1001 al 1012 |
| Epic 11 | Documentación y Entregables | ISSUE-1101 al 1106 |

---

## 🏗️ Epic 1: Infraestructura y DevOps

### ISSUE-101: Configurar Repositorio Monorepo
- **Prioridad:** 🔴 Crítica
- **Descripción:** Inicializar la estructura base del repositorio que contendrá todos los microservicios.
- **Tareas:**
  - [ ] Crear repositorio **público** en GitHub con nombre descriptivo (ej. `agm-backend`)
  - [ ] Crear ramas principales: `main` (producción estable) y `develop` (integración activa)
  - [ ] Configurar reglas de protección de ramas: requerir PR para fusionar a `main`
  - [ ] Crear estructura de carpetas en la raíz:
    ```
    /ms-auth
    /ms-periodos
    /ms-alumnos
    /ms-calificaciones
    /ms-asistencias
    /ms-notificaciones
    /ms-reportes
    /proto
    /frontend   ← (si aplica punto extra)
    ```
  - [ ] Agregar `.gitignore` global que excluya `.env`, `__pycache__`, `node_modules`, `*.pyc`
  - [ ] Crear `README.md` inicial con nombre del proyecto e integrantes
- **Criterio de aceptación:** El repositorio existe en GitHub, es público, tiene las 2 ramas y la estructura de carpetas correcta.

---

### ISSUE-102: Contenedorización con Docker por Microservicio
- **Prioridad:** 🔴 Crítica
- **Descripción:** Crear `Dockerfile` individual para cada uno de los 7 microservicios.
- **Tareas:**
  - [ ] Crear `Dockerfile` en cada carpeta `/ms-*` basado en imagen oficial de Python (`python:3.12-slim`)
  - [ ] Asegurarse de que cada Dockerfile copie `requirements.txt` e instale dependencias antes de copiar el resto del código (para aprovechar caché de capas)
  - [ ] Exponer el puerto REST y el puerto gRPC en cada Dockerfile
  - [ ] Verificar que cada imagen se construya sin errores con `docker build`
- **Criterio de aceptación:** `docker build` exitoso en cada microservicio de forma independiente.

---

### ISSUE-103: Archivo `docker-compose.yml` Unificado
- **Prioridad:** 🔴 Crítica
- **Descripción:** Crear archivo en la raíz para levantar todo el sistema con un único comando.
- **Tareas:**
  - [ ] Definir un servicio en `docker-compose.yml` por cada microservicio (7 en total)
  - [ ] Definir contenedores de base de datos separados (imagen `mysql:8.0`, `utf8mb4`, un esquema por servicio):
    - `db-auth` → base `agm_auth_db` (ms-auth)
    - `db-periodos` → `agm_periodos_db` (ms-periodos)
    - `db-alumnos` → `agm_alumnos_db` (ms-alumnos)
    - `db-calificaciones` → `agm_calificaciones_db` (ms-calificaciones)
    - `db-asistencias` → `agm_asistencias_db` (ms-asistencias) + contenedor `redis` (sesiones en vivo)
    - `db-notificaciones` → `agm_notificaciones_db` (ms-notificaciones)
    - `db-reportes` → `agm_reportes_db` (ms-reportes)
  - [ ] Configurar red Docker interna (`bridge`) para comunicación entre contenedores por nombre de servicio
  - [ ] Definir `volumes` persistentes para cada base de datos
  - [ ] Leer variables de entorno desde archivos `.env` por servicio usando `env_file`
  - [ ] Configurar `depends_on` para que cada microservicio espere a su base de datos
  - [ ] Agregar `healthcheck` a los contenedores de bases de datos
  - [ ] Probar que `docker compose up --build` (o `docker-compose up --build`) levanta todo el sistema correctamente
- **Criterio de aceptación:** Un solo `docker compose up --build` levanta los 7 MS + sus BDs sin errores.

---

### ISSUE-104: Archivos `.env.example` por Microservicio
- **Prioridad:** 🟠 Alta
- **Descripción:** Documentar todas las variables de entorno necesarias sin exponer valores reales.
- **Tareas:**
  - [ ] Crear `.env.example` en cada carpeta `/ms-*` con todas las variables requeridas, por ejemplo:
    ```env
    # .env.example para ms-auth (ver también CONTEXTO_GLOBAL sección 6.9)
    SECRET_KEY=your-secret-key-here
    DEBUG=False
    ALLOWED_HOSTS=*
    DB_HOST=db-auth
    DB_PORT=3306
    DB_NAME=agm_auth_db
    DB_USER=root
    DB_PASSWORD=change-me
    DB_CHARSET=utf8mb4
    REST_PORT=8001
    GRPC_PORT=50051
    ```
  - [ ] Asegurarse de que los `.env` reales **nunca** se suban al repositorio (verificar `.gitignore`)
  - [ ] Documentar en el README cómo copiar `.env.example` a `.env` y completar los valores
- **Criterio de aceptación:** `.env.example` presente en cada MS, sin valores reales. `.env` en `.gitignore`.

---

### ISSUE-105: Configuración de CORS en todos los Microservicios
- **Prioridad:** 🟠 Alta
- **Descripción:** Habilitar CORS correctamente para permitir peticiones del frontend y entre servicios.
- **Tareas:**
  - [ ] Instalar `django-cors-headers` en cada MS de Django
  - [ ] Configurar `CORS_ALLOWED_ORIGINS` en `settings.py` con las URLs del frontend y del API Gateway
  - [ ] En producción: restringir CORS solo a los orígenes autorizados (no usar `CORS_ALLOW_ALL_ORIGINS=True`)
  - [ ] Verificar que las peticiones preflight OPTIONS respondan correctamente
- **Criterio de aceptación:** Las peticiones desde el frontend en producción no reciben errores de CORS.

---

### ISSUE-106: Despliegue en Plataforma Cloud (Producción)
- **Prioridad:** 🔴 Crítica
- **Descripción:** Desplegar todos los microservicios en un entorno de nube con URLs públicas y HTTPS.
- **Tareas:**
  - [ ] Elegir plataforma de despliegue (Railway / Render / Fly.io: Docker + **MySQL** gestionado o contenedor MySQL 8)
  - [ ] Crear proyecto en la plataforma cloud y conectar repositorio GitHub
  - [ ] Desplegar cada microservicio como servicio independiente
  - [ ] Configurar bases de datos gestionadas (o contenedores) en la plataforma
  - [ ] Configurar variables de entorno de producción en la plataforma (NO en el repositorio)
  - [ ] Verificar que todas las URLs sean HTTPS (las plataformas recomendadas lo proveen automáticamente)
  - [ ] Documentar las URLs públicas de cada MS en el README
- **Criterio de aceptación:** Los 7 MS tienen URL pública accesible vía HTTPS al momento de la presentación.

---

### ISSUE-107: API Gateway / Proxy Reverso (Recomendado)
- **Prioridad:** 🟡 Media
- **Descripción:** Implementar un punto de entrada único para el cliente que enrute peticiones a cada microservicio.
- **Tareas:**
  - [ ] Implementar **Nginx** como API Gateway / proxy reverso (punto de entrada único; ver `CONTEXTO_GLOBAL_PROYECTO.md`)
  - [ ] Configurar rutas de enrutamiento: `/auth/*` → ms-auth, `/periodos/*` → ms-periodos, etc.
  - [ ] Agregar el gateway al `docker-compose.yml`
  - [ ] Configurar CORS en el gateway (en lugar de en cada MS individualmente si se centraliza)
  - [ ] Agregar el gateway al despliegue en producción
- **Criterio de aceptación:** El cliente puede acceder a todos los MS a través de una sola URL base.

---

## ⚡ Epic 2: Arquitectura y Comunicación gRPC

### ISSUE-201: Definición de Contratos `.proto` por Microservicio
- **Prioridad:** 🔴 Crítica
- **Descripción:** Redactar los archivos `.proto` que definen la interfaz gRPC de cada MS que expone métodos internos.
- **Tareas:**
  - [ ] Crear `/proto/auth.proto` con servicios: `ValidateToken`, `GetUserById`, `CheckRole`
  - [ ] Crear `/proto/periodos.proto` con servicios: `GetMateriaById`, `GetMateriasByDocente`, `GetPeriodoActivo`
  - [ ] Crear `/proto/alumnos.proto` con servicios: `GetAlumnosByMateria`, `GetAlumnoById`, `IsAlumnoEnMateria`
  - [ ] Crear `/proto/calificaciones.proto` con servicios: `GetConcentrado`, `GetPromedioAlumno`, `GetEstadisticasMateria`
  - [ ] Crear `/proto/asistencias.proto` con servicios: `GetAsistenciaAlumno`, `GetEstadisticasAsistencia`
  - [ ] Crear `/proto/notificaciones.proto` con servicios: `SendBienvenida`, `SendBajaNotif`, `SendCierreMateria`
  - [ ] Crear `/proto/reportes.proto` con servicios: `GenerateReport`, `GetHistorialDocente`
  - [ ] Usar `syntax = "proto3"` en todos los archivos
  - [ ] Definir mensajes de request y response correctamente tipados para cada RPC
  - [ ] Versionar todos los `.proto` en la carpeta `/proto` del repositorio
- **Criterio de aceptación:** 7 archivos `.proto` presentes en `/proto`, sintácticamente válidos (compilar con `grpc_tools.protoc` / `protoc` sin errores).

---

### ISSUE-202: Generación de Código gRPC en Django (Servidor)
- **Prioridad:** 🔴 Crítica
- **Descripción:** Configurar la generación de código servidor gRPC en cada microservicio Django que expone métodos.
- **Tareas:**
  - [ ] Agregar `grpcio` y `grpcio-tools` a `requirements.txt` de cada MS correspondiente
  - [ ] Crear script `generate_proto.sh` en cada MS para regenerar el código desde el `.proto`:
    ```bash
    python -m grpc_tools.protoc -I../../proto --python_out=. --grpc_python_out=. ../../proto/auth.proto
    ```
  - [ ] Implementar la clase `Servicer` en cada MS que hereda del stub generado y sobreescribe cada método RPC
  - [ ] Crear un servidor gRPC en un `management command` de Django o en un proceso independiente (hilo o proceso separado)
  - [ ] Asignar puertos exclusivos por MS (rango 50051–50057): ms-auth→50051, ms-periodos→50052, ms-alumnos→50053, ms-calificaciones→50054, ms-asistencias→50055, ms-notificaciones→50056, ms-reportes→50057
  - [ ] El servidor gRPC debe iniciarse junto con el servidor REST en el contenedor Docker
- **Criterio de aceptación:** Cada MS levanta su servidor gRPC en el puerto asignado y responde a llamadas de prueba.

---

### ISSUE-203: Implementación de Clientes gRPC entre Microservicios
- **Prioridad:** 🔴 Crítica
- **Descripción:** Configurar los clientes gRPC en cada MS que necesita consumir datos de otro MS.
- **Tareas:**
  - [ ] Identificar todas las dependencias inter-servicio (ej. ms-calificaciones llama a ms-alumnos para obtener datos de alumnos)
  - [ ] En cada MS consumidor, generar el stub cliente desde el `.proto` correspondiente
  - [ ] Crear módulo `grpc_clients.py` en cada MS con funciones helper para cada llamada gRPC (ej. `get_alumno_by_id(alumno_id)`)
  - [ ] Configurar la dirección del servidor gRPC destino mediante variables de entorno (ej. `MS_ALUMNOS_GRPC_HOST=ms-alumnos:50053`)
  - [ ] Manejar errores gRPC con los códigos correctos: `StatusCode.NOT_FOUND`, `StatusCode.UNAUTHENTICATED`, `StatusCode.INTERNAL`
  - [ ] Agregar timeout a todas las llamadas gRPC para evitar bloqueos indefinidos
- **Criterio de aceptación:** Al menos 3 pares de microservicios se comunican exitosamente via gRPC (demostrable en presentación).

---

### ISSUE-204: Testing de Comunicación gRPC
- **Prioridad:** 🟠 Alta
- **Descripción:** Verificar y documentar las llamadas gRPC entre servicios.
- **Tareas:**
  - [ ] Instalar y usar `grpcurl` o `grpc_cli` para probar manualmente los endpoints gRPC
  - [ ] Crear script de prueba básico en Python para cada método gRPC expuesto
  - [ ] Documentar los comandos de prueba en el Manual Técnico
  - [ ] Verificar que los errores gRPC se propaguen correctamente y no rompan el MS consumidor
- **Criterio de aceptación:** Cada método gRPC puede probarse manualmente y está documentado.

---

## 🔐 Epic 3: ms-auth Auth & Users

### ISSUE-301: Configuración Base del Proyecto Django (ms-auth)
- **Prioridad:** 🔴 Crítica
- **Descripción:** Inicializar el proyecto Django para el microservicio de autenticación.
- **Tareas:**
  - [ ] Crear proyecto Django en `/ms-auth/` con `django-admin startproject config .`
  - [ ] Instalar dependencias: `djangorestframework`, `djangorestframework-simplejwt`, `mysqlclient`, `django-cors-headers`, `grpcio`, `grpcio-tools`, `python-decouple`
  - [ ] Configurar `settings.py`: **MySQL 8** (`ENGINE=django.db.backends.mysql`, `utf8mb4`), apps instaladas, REST_FRAMEWORK con autenticación JWT
  - [ ] Configurar base de datos `agm_auth_db` (MySQL, contenedor `db-auth` o equivalente)
  - [ ] Crear modelo de usuario personalizado (`AbstractBaseUser`) con campos: `email`, `password`, `rol` (admin/docente/alumno), `nombre`, `activo`
  - [ ] Crear y aplicar migraciones iniciales
  - [ ] Configurar `Dockerfile` y verificar que corra con `gunicorn`
- **Criterio de aceptación:** El MS levanta, se conecta a la BD y las migraciones corren sin errores.

---

### ISSUE-302: Endpoint de Login con JWT
- **Prioridad:** 🔴 Crítica
- **Descripción:** Implementar autenticación por correo y contraseña con tokens JWT.
- **Tareas:**
  - [ ] `POST /auth/login` → recibe `email` y `password`, retorna `access_token` y `refresh_token`
  - [ ] Configurar `simplejwt` con expiración de `access_token` (15–60 min) y `refresh_token` (7 días)
  - [ ] Incluir en el payload del JWT: `user_id`, `email`, `rol`, `nombre`
  - [ ] Retornar 401 si las credenciales son incorrectas o el usuario está inactivo
  - [ ] `POST /auth/refresh-token` → recibe `refresh_token`, retorna nuevo `access_token`
  - [ ] `GET /auth/me` → retorna los datos del usuario autenticado (requiere JWT válido)
- **Criterio de aceptación:** Login exitoso devuelve JWT válido; token inválido devuelve 401.

---

### ISSUE-303: Recuperación de Contraseña
- **Prioridad:** 🟠 Alta
- **Descripción:** Implementar flujo de restablecimiento de contraseña vía correo electrónico.
- **Tareas:**
  - [ ] `POST /auth/forgot-password` → recibe `email`, genera token de un solo uso (UUID + expiración), llama via gRPC a ms-notificaciones para enviar el correo
  - [ ] Modelo `PasswordResetToken`: campos `user`, `token` (UUID), `expira_en`, `usado`
  - [ ] `POST /auth/reset-password` → recibe `token` y `nueva_password`, valida que el token exista, no haya expirado y no haya sido usado; actualiza la contraseña y marca el token como usado
  - [ ] El token de reset debe expirar en 1 hora
  - [ ] Retornar 400 si el token es inválido o ya fue usado
- **Criterio de aceptación:** El flujo completo de reset de contraseña funciona end-to-end (incluyendo el correo).

---

### ISSUE-304: Control de Acceso por Roles (RBAC)
- **Prioridad:** 🔴 Crítica
- **Descripción:** Implementar permisos basados en roles para proteger endpoints.
- **Tareas:**
  - [ ] Crear permisos personalizados de DRF: `IsAdminRole`, `IsDocenteRole`, `IsAlumnoRole`
  - [ ] Crear middleware o decorator `require_role` para ser usado en las vistas de otros MS
  - [ ] Documentar cómo los otros MS deben usar gRPC (`ValidateToken` + `CheckRole`) para verificar el JWT antes de procesar peticiones
- **Criterio de aceptación:** Un alumno no puede acceder a endpoints de administrador. Un docente no puede acceder a endpoints de alumno.

---

### ISSUE-305: Servidor gRPC de Auth (Métodos Internos)
- **Prioridad:** 🔴 Crítica
- **Descripción:** Exponer los métodos gRPC que los demás MS usarán para validar autenticación.
- **Tareas:**
  - [ ] Implementar `ValidateToken(token) → UserClaims`: valida el JWT y retorna los claims del usuario
  - [ ] Implementar `GetUserById(userId) → UserProfile`: retorna nombre, email y rol de un usuario por ID
  - [ ] Implementar `CheckRole(userId, role) → bool`: verifica si el usuario tiene el rol indicado
  - [ ] Puerto gRPC: **50051**
- **Criterio de aceptación:** Los 3 métodos gRPC responden correctamente en el puerto 50051.

---

### ISSUE-306: Gestión de Usuarios (Admin)
- **Prioridad:** 🟠 Alta
- **Descripción:** Endpoints para que el Admin gestione el catálogo de usuarios del sistema.
- **Tareas:**
  - [ ] `GET /usuarios` → listado paginado de todos los usuarios (solo Admin)
  - [ ] `GET /usuarios/:id` → detalle de un usuario
  - [ ] `PUT /usuarios/:id` → actualizar datos de un usuario (nombre, activo)
  - [ ] `POST /usuarios/:id/reset-password` → Admin fuerza reset de contraseña de un usuario
  - [ ] `DELETE /usuarios/:id` → desactivar (soft delete) un usuario
- **Criterio de aceptación:** El admin puede gestionar usuarios. Los endpoints están protegidos por rol.

---

### ISSUE-307: Creación de Usuarios (integración con otros MS)
- **Prioridad:** 🟠 Alta
- **Descripción:** Endpoint para que otros MS (como ms-alumnos) creen usuarios en el sistema al importar docentes/alumnos.
- **Tareas:**
  - [ ] `POST /usuarios` → crea un nuevo usuario con rol, email y contraseña temporal; retorna el `user_id`
  - [ ] Este endpoint debe ser consumible únicamente desde microservicios internos (validar por API key o JWT de servicio)
  - [ ] Al crear un alumno, generar una clave única segura (UUID o similar) como contraseña inicial
- **Criterio de aceptación:** ms-alumnos puede crear usuarios en ms-auth al importar alumnos.

---

### ISSUE-308: Cierre de Sesión (Invalidación de Token)
- **Prioridad:** 🟡 Media
- **Descripción:** Implementar logout con invalidación del refresh token.
- **Tareas:**
  - [ ] `POST /auth/logout` → recibe `refresh_token`, lo agrega a una lista negra (blacklist)
  - [ ] Configurar `simplejwt` con `ROTATE_REFRESH_TOKENS=True` y blacklist activada
  - [ ] Migrar la app `token_blacklist` de simplejwt
- **Criterio de aceptación:** Después del logout, el refresh token no puede usarse para obtener nuevos access tokens.

---

## 📅 Epic 4: ms-periodos Periodos & Materias

### ISSUE-401: Configuración Base del Proyecto Django (ms-periodos)
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] Inicializar proyecto Django en `/ms-periodos/`
  - [ ] Dependencias adicionales: `pdfplumber` o `pypdf2` + `pdfminer.six` (para parsing de PDF)
  - [ ] Configurar base de datos `agm_periodos_db` (MySQL 8)
  - [ ] Crear modelos: `Periodo` (nombre, fecha_inicio, fecha_fin, plan_estudios, activo) y `Materia` (nrc, nombre, seccion, clave, docente_id, horario, periodo)
  - [ ] Crear y aplicar migraciones
- **Criterio de aceptación:** El MS levanta y se conecta a su base de datos.

---

### ISSUE-402: CRUD de Periodos Académicos
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] `GET /periodos` → listar todos los periodos paginados
  - [ ] `POST /periodos` → crear nuevo periodo (solo Admin)
  - [ ] `PUT /periodos/:id` → editar periodo (solo Admin)
  - [ ] `DELETE /periodos/:id` → eliminar periodo (solo si no tiene materias asociadas)
  - [ ] `POST /periodos/:id/activar` → activar un periodo y **desactivar automáticamente** cualquier otro que esté activo (regla de negocio crítica: solo 1 activo a la vez)
  - [ ] Validar en creación/edición que las fechas sean coherentes (inicio < fin)
  - [ ] Proteger todos los endpoints de escritura con rol Admin (llamada gRPC a ms-auth para validar)
- **Criterio de aceptación:** No pueden existir 2 periodos activos simultáneamente. La validación es a nivel de base de datos (constraint único) y de lógica de negocio.

---

### ISSUE-403: Importación de Materias desde PDF
- **Prioridad:** 🔴 Crítica
- **Descripción:** El endpoint más complejo de `ms-periodos`: procesar un PDF oficial y extraer datos automáticamente.
- **Tareas:**
  - [ ] `POST /periodos/importar` → recibe archivo PDF (multipart/form-data) y el ID del periodo destino
  - [ ] Implementar función de parsing con `pdfplumber`:
    - Extraer NRC (código único de materia)
    - Extraer nombre de materia
    - Extraer sección
    - Extraer clave de materia
    - Extraer nombre de docente asignado
    - Extraer horario (días y horas)
  - [ ] Normalizar y limpiar los datos extraídos (remover espacios extras, corregir encoding)
  - [ ] Asociar docentes por nombre usando llamada gRPC a ms-alumnos (`GetDocenteByNombre`) — o almacenar solo el nombre si el docente aún no existe
  - [ ] Persistir las materias en la base de datos del periodo indicado
  - [ ] Retornar resumen: cuántas materias se importaron, cuántas fallaron y por qué
  - [ ] Manejar errores: PDF corrupto, formato inesperado, NRC duplicado
- **Criterio de aceptación:** Se puede subir el PDF oficial de la BUAP y el sistema extrae e inserta las materias correctamente.

---

### ISSUE-404: Gestión del Catálogo de Materias
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] `GET /materias?periodo=:id` → listar materias de un periodo (paginado, con búsqueda por NRC o nombre)
  - [ ] `GET /materias/:id` → detalle de una materia
  - [ ] `PUT /materias/:id` → editar materia manualmente (solo Admin)
  - [ ] `DELETE /materias/:id` → eliminar materia (solo si no tiene alumnos inscritos)
- **Criterio de aceptación:** CRUD completo de materias funcional.

---

### ISSUE-405: Servidor gRPC de Periodos & Materias
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] Implementar `GetMateriaById(materiaId) → MateriaInfo`
  - [ ] Implementar `GetMateriasByDocente(docenteId) → [Materia]`
  - [ ] Implementar `GetPeriodoActivo() → PeriodoInfo`
  - [ ] Puerto gRPC: **50052**
- **Criterio de aceptación:** Los 3 métodos gRPC responden correctamente en el puerto 50052.

---

### ISSUE-406: Validación de JWT en ms-periodos
- **Prioridad:** 🔴 Crítica
- **Descripción:** Cada endpoint protegido de `ms-periodos` debe validar el JWT usando gRPC contra `ms-auth`.
- **Tareas:**
  - [ ] Crear decorador/middleware `grpc_jwt_required` que extrae el token del header `Authorization: Bearer <token>`, llama a `ValidateToken` en ms-auth via gRPC, y retorna 401 si no es válido
  - [ ] Aplicar este decorador a todos los endpoints que requieren autenticación
- **Criterio de aceptación:** Peticiones sin JWT válido reciben 401.

---

### ISSUE-407: Endpoint de Periodo Activo Público
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] `GET /periodos/activo` → retorna los datos del periodo actualmente activo (sin autenticación o con cualquier rol)
  - [ ] Retornar 404 si no hay ningún periodo activo
- **Criterio de aceptación:** Cualquier usuario autenticado puede consultar el periodo activo.

---

### ISSUE-408: Paginación y Búsqueda en Listados
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] Implementar paginación (`?page=1&limit=10`) en `GET /periodos` y `GET /materias`
  - [ ] Implementar filtro de búsqueda por nombre/NRC en `GET /materias`
  - [ ] Formato de respuesta consistente: `{ "success": true, "data": [...], "pagination": { "page": 1, "total": N } }`
- **Criterio de aceptación:** Los listados están paginados y son buscables.

---

## 👥 Epic 5: ms-alumnos Docentes & Alumnos

### ISSUE-501: Configuración Base del Proyecto Django (ms-alumnos)
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] Inicializar proyecto Django en `/ms-alumnos/`
  - [ ] Dependencias: `openpyxl`, `pandas`, `pdfplumber`, `grpcio`, `grpcio-tools`
  - [ ] Configurar base de datos `agm_alumnos_db` (MySQL 8)
  - [ ] Crear modelos:
    - `Docente`: nombre, email_institucional, cubiculo, usuario_id (referencia a ms-auth)
    - `Alumno`: matricula, nombre, email, tipo_formacion, materia_id, activo, fecha_baja
    - `InscripcionMateria`: alumno, materia_id (FK lógica), fecha_inscripcion, activo
- **Criterio de aceptación:** El MS levanta y se conecta a su base de datos.

---

### ISSUE-502: Importación de Docentes desde PDF
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] `POST /docentes/importar` → recibe PDF del directorio institucional
  - [ ] Parsear el PDF con `pdfplumber`: extraer nombre completo, correo institucional, cubículo
  - [ ] Por cada docente extraído:
    - Crear usuario en ms-auth via gRPC o HTTP interno (con rol `docente` y contraseña temporal)
    - Guardar el docente en la BD local con referencia al `usuario_id`
    - Llamar a ms-notificaciones para enviar correo de bienvenida al docente con sus credenciales
  - [ ] Manejar duplicados: si el email ya existe, actualizar datos sin crear duplicado
  - [ ] Retornar resumen de importación (importados, actualizados, fallidos)
- **Criterio de aceptación:** El PDF de directorio docente BUAP se procesa y los docentes quedan registrados.

---

### ISSUE-503: CRUD de Docentes
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] `GET /docentes` → listado paginado con búsqueda por nombre o email (solo Admin)
  - [ ] `GET /docentes/:id` → detalle de docente
  - [ ] `PUT /docentes/:id` → actualizar datos de docente (solo Admin)
  - [ ] `POST /docentes/:id/reset-password` → Admin resetea contraseña del docente (llama a ms-auth)
- **Criterio de aceptación:** Admin puede gestionar el catálogo de docentes.

---

### ISSUE-504: Importación de Alumnos desde Excel/CSV
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] `POST /alumnos/importar/:materiaId` → recibe archivo Excel/CSV con lista de alumnos
  - [ ] Parsear con `pandas` o `openpyxl`: extraer matrícula, nombre completo, email, tipo de formación
  - [ ] Mostrar **vista previa** de los datos antes de confirmar la importación (`?preview=true`)
  - [ ] Al confirmar importación:
    - Crear usuario en ms-auth via gRPC con rol `alumno` y clave única generada
    - Guardar alumno en BD local
    - Inscribir alumno en la materia indicada
    - Llamar a ms-notificaciones via gRPC (`SendBienvenida`) para enviar correo con la clave única
  - [ ] Manejar duplicados: si la matrícula ya existe en esa materia, ignorar sin error
  - [ ] Retornar resumen de importación
- **Criterio de aceptación:** La importación Excel crea alumnos, sus usuarios y envía correos de bienvenida.

---

### ISSUE-505: Gestión de Alumnos por Materia
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] `GET /alumnos/materia/:materiaId` → listado de alumnos inscritos en una materia (paginado)
  - [ ] `GET /alumnos/:id` → detalle de alumno
  - [ ] Verificar que solo el docente asignado a esa materia pueda ver sus alumnos (validar con gRPC a ms-periodos)
- **Criterio de aceptación:** El docente puede consultar sus alumnos por materia.

---

### ISSUE-506: Baja de Materia (Operación Irreversible)
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] `DELETE /alumnos/:id/baja` → el alumno se da de baja de una materia específica
  - [ ] Validar que el alumno solo puede darse de baja de una materia **una vez** (campo `baja_solicitada` en modelo)
  - [ ] Marcar la inscripción como inactiva (soft delete, nunca borrar el registro)
  - [ ] Llamar a ms-notificaciones via gRPC (`SendBajaNotif`) para notificar al docente
  - [ ] El alumno dado de baja no debe aparecer en el concentrado de calificaciones ni en el pase de lista
  - [ ] Retornar 400 si el alumno ya solicitó baja previamente
- **Criterio de aceptación:** La baja es irreversible, notifica al docente y el alumno pierde acceso a la materia.

---

### ISSUE-507: Servidor gRPC de Docentes & Alumnos
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] Implementar `GetAlumnosByMateria(materiaId) → [AlumnoInfo]`
  - [ ] Implementar `GetAlumnoById(alumnoId) → AlumnoInfo`
  - [ ] Implementar `IsAlumnoEnMateria(alumnoId, materiaId) → bool` (solo retorna `true` si el alumno está activo, no dado de baja)
  - [ ] Puerto gRPC: **50053**
- **Criterio de aceptación:** Los 3 métodos gRPC responden correctamente en el puerto 50053.

---

### ISSUE-508: Dashboard del Alumno (Datos Base)
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] `GET /alumnos/me/materias` → lista de materias en las que el alumno autenticado está inscrito (activas)
  - [ ] Incluir en la respuesta: NRC, nombre de materia, docente (nombre), sección
  - [ ] Protegido con rol `alumno`
- **Criterio de aceptación:** El alumno autenticado puede ver sus materias activas.

---

### ISSUE-509: Validación de JWT en ms-alumnos
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] Implementar el mismo decorador `grpc_jwt_required` que en ms-periodos
  - [ ] Aplicar a todos los endpoints protegidos
- **Criterio de aceptación:** Peticiones sin JWT válido reciben 401.

---

## 📊 Epic 6: ms-calificaciones Calificaciones & Ponderaciones

### ISSUE-601: Configuración Base del Proyecto Django (ms-calificaciones)
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] Inicializar proyecto Django en `/ms-calificaciones/`
  - [ ] Dependencias: `openpyxl`, `grpcio`, `grpcio-tools`
  - [ ] Configurar base de datos `agm_calificaciones_db` (MySQL 8)
  - [ ] Crear modelos:
    - `Ponderacion`: materia_id, nombre_categoria (ej. "Exámenes"), porcentaje
    - `Actividad`: ponderacion (FK), nombre, descripcion, fecha
    - `Calificacion`: actividad (FK), alumno_id, calificacion (decimal 0-10)
- **Criterio de aceptación:** El MS levanta y se conecta a su base de datos.

---

### ISSUE-602: Configuración de Ponderaciones
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] `GET /ponderaciones/:materiaId` → obtener ponderaciones configuradas de una materia
  - [ ] `POST /ponderaciones/:materiaId` → crear ponderaciones (recibe lista de categorías con porcentajes)
  - [ ] `PUT /ponderaciones/:materiaId` → actualizar ponderaciones
  - [ ] **Validar que la suma de todos los porcentajes sea exactamente 100%** (retornar 400 si no)
  - [ ] Validar que solo el docente de esa materia pueda configurar ponderaciones (llamada gRPC a ms-periodos para verificar)
  - [ ] Permitir importación de ponderaciones desde Excel (`POST /ponderaciones/:materiaId/importar`)
- **Criterio de aceptación:** No se pueden guardar ponderaciones que no sumen exactamente 100%.

---

### ISSUE-603: Gestión de Actividades
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] `POST /actividades` → crear una actividad bajo una categoría de ponderación (ej. "Examen Parcial 1" bajo "Exámenes")
  - [ ] `GET /actividades?materia=:id` → listar actividades de una materia organizadas por categoría
  - [ ] `PUT /actividades/:id` → editar nombre/descripción de actividad
  - [ ] `DELETE /actividades/:id` → eliminar actividad (solo si no tiene calificaciones asignadas)
- **Criterio de aceptación:** El docente puede crear y gestionar actividades por categoría de ponderación.

---

### ISSUE-604: Registro Individual de Calificaciones
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] `POST /calificaciones` → asignar calificación a un alumno en una actividad específica
  - [ ] `PUT /calificaciones/:id` → actualizar calificación (mientras la materia no esté cerrada con lista final impresa)
  - [ ] Validar que el alumno pertenece a la materia (llamada gRPC a ms-alumnos: `IsAlumnoEnMateria`)
  - [ ] Validar rango de calificación (0 a 10, con hasta 2 decimales)
- **Criterio de aceptación:** Se pueden asignar y editar calificaciones individuales.

---

### ISSUE-605: Importación Masiva de Calificaciones desde Excel
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] `POST /calificaciones/importar` → recibe Excel con columnas: matrícula, actividad_id, calificación
  - [ ] Parsear con `openpyxl`, validar datos antes de insertar
  - [ ] Retornar resumen de importación (exitosos, fallidos con motivo)
- **Criterio de aceptación:** Se puede importar calificaciones masivamente desde Excel.

---

### ISSUE-606: Cálculo de Promedios Ponderados
- **Prioridad:** 🔴 Crítica
- **Descripción:** Motor de cálculo del promedio final de cada alumno según las ponderaciones configuradas.
- **Tareas:**
  - [ ] Implementar función `calcular_promedio_ponderado(alumno_id, materia_id)`:
    - Para cada categoría de ponderación, calcular el promedio de calificaciones del alumno en las actividades de esa categoría
    - Multiplicar por el porcentaje de la categoría
    - Sumar todos los resultados → promedio real
  - [ ] Implementar regla de redondeo institucional:
    - Fracción `>= 0.5` → redondear al entero superior (ej. 7.5 → 8)
    - Fracción `< 0.5` → redondear al entero inferior (ej. 7.4 → 7)
  - [ ] El cálculo debe ejecutarse en tiempo real (no precalculado) o invalidarse cuando se actualiza una calificación
- **Criterio de aceptación:** El promedio ponderado se calcula correctamente. La regla de redondeo es correcta.

---

### ISSUE-607: Vista del Concentrado de Calificaciones
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] `GET /concentrado/:materiaId` → retorna tabla completa con:
    - Nombre y matrícula del alumno (obtenidos via gRPC de ms-alumnos)
    - Calificaciones por actividad
    - Promedio real (decimal)
    - Promedio redondeado (entero según regla institucional)
  - [ ] Solo accesible para el docente de la materia o Admin
- **Criterio de aceptación:** El concentrado muestra correctamente todos los alumnos con sus promedios reales y redondeados.

---

### ISSUE-608: Control de Cierre de Materia
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] Modelo `EstadoMateria`: materia_id, cerrada (bool), lista_impresa (bool)
  - [ ] `POST /materias/:id/cerrar` → marca la materia como cerrada; llama a ms-notificaciones (`SendCierreMateria`) para notificar a alumnos
  - [ ] `POST /materias/:id/imprimir-lista` → marca `lista_impresa = True`; después de esto, **no se permiten más cambios en calificaciones**
  - [ ] Bloquear edición de calificaciones si `lista_impresa = True`
- **Criterio de aceptación:** Las calificaciones no pueden modificarse después de que se imprime la lista final.

---

### ISSUE-609: Servidor gRPC de Calificaciones
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] Implementar `GetConcentrado(materiaId) → [AlumnoCalif]`
  - [ ] Implementar `GetPromedioAlumno(alumnoId, materiaId) → float`
  - [ ] Implementar `GetEstadisticasMateria(materiaId) → Stats` (promedio grupal, aprobados/reprobados)
  - [ ] Puerto gRPC: **50054**
- **Criterio de aceptación:** Los 3 métodos gRPC responden correctamente en el puerto 50054.

---

## 📱 Epic 7: ms-asistencias Asistencias QR

### ISSUE-701: Configuración Base del Proyecto Django (ms-asistencias)
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] Inicializar proyecto Django en `/ms-asistencias/`
  - [ ] Dependencias: `redis`, `django-redis`, `grpcio`, `grpcio-tools`, `cryptography` (para cifrado del QR)
  - [ ] Configurar BD: `agm_asistencias_db` (MySQL 8) + Redis (para sesiones en vivo)
  - [ ] Crear modelos:
    - `SesionAsistencia`: materia_id, docente_id, inicio, fin, activa
    - `RegistroAsistencia`: sesion (FK), alumno_id, timestamp_registro, estado (Presente/Retardo)
- **Criterio de aceptación:** El MS levanta, se conecta a **MySQL** y a Redis.

---

### ISSUE-702: Gestión de Sesiones de Asistencia
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] `POST /sesiones/iniciar` → el docente abre una sesión para una materia:
    - Crear sesión en MySQL (`agm_asistencias_db`)
    - Almacenar en Redis: `sesion:{sesion_id}` con TTL de 600 segundos (10 minutos)
    - Solo puede haber una sesión activa por materia a la vez
  - [ ] `DELETE /sesiones/:id/cerrar` → el docente cierra manualmente la sesión antes de que expire
  - [ ] Cierre automático por Redis TTL (cuando el TTL expira, la sesión se marca como inactiva en MySQL mediante worker, signal o tarea periódica)
  - [ ] `GET /sesiones/:materiaId/activa` → consultar si hay sesión activa para esa materia
- **Criterio de aceptación:** Las sesiones duran máximo 10 minutos y se cierran automáticamente.

---

### ISSUE-703: Generación de Token QR del Alumno
- **Prioridad:** 🔴 Crítica
- **Descripción:** El backend provee el payload cifrado que el alumno usará para generar su QR dinámico.
- **Tareas:**
  - [ ] `GET /qr/generate` → el alumno autenticado solicita su payload QR:
    - Genera token con: `alumno_id`, `sesion_id` (si hay sesión activa para su materia), `timestamp`, firma HMAC
    - El token tiene validez corta (ej. 30 segundos)
    - Retornar el token como string para que el frontend lo encode en QR
  - [ ] El token debe renovarse automáticamente (el frontend debe llamar este endpoint cada 30 segundos)
- **Criterio de aceptación:** El payload QR cambia cada 30 segundos, haciendo inútil una captura de pantalla.

---

### ISSUE-704: Registro de Asistencia (Validación del QR)
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] `POST /asistencias/registrar` → el docente envía el contenido del QR escaneado:
    - Verificar firma HMAC del token
    - Verificar que el token no haya expirado (timestamp + 30s)
    - Verificar en Redis que el token NO haya sido usado previamente (**anti-replay**): `SET qr_used:{token_hash} 1 EX 60`
    - Verificar que haya una sesión activa en Redis para esa materia
    - Calcular estado según tiempo transcurrido desde inicio de sesión:
      - `Presente`: registro en los primeros 5 minutos
      - `Retardo`: registro entre 5 y 10 minutos
    - Registrar asistencia en MySQL
    - Marcar el token como usado en Redis
  - [ ] Retornar 400 si el QR es inválido, expirado, ya fue usado o la sesión ya cerró
- **Criterio de aceptación:** Anti-replay funciona. El estado Presente/Retardo se calcula correctamente.

---

### ISSUE-705: Consulta de Asistencias
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] `GET /asistencias/:materiaId/hoy` → asistencias del día en curso para esa materia
  - [ ] `GET /asistencias/:materiaId/historial` → historial completo de asistencias de la materia (paginado, filtrable por fecha)
  - [ ] `GET /asistencias/alumno/:alumnoId/materia/:materiaId` → historial de asistencias de un alumno específico en una materia
- **Criterio de aceptación:** El docente puede consultar el historial completo de asistencias.

---

### ISSUE-706: Estadísticas de Asistencia en Tiempo Real
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] Durante una sesión activa, `GET /sesiones/:id/stats` → retorna en tiempo real: total de alumnos, presentes, retardos, ausentes
  - [ ] Usar Redis para mantener contadores en tiempo real durante la sesión
- **Criterio de aceptación:** Durante el pase de lista, el docente ve estadísticas actualizadas en tiempo real.

---

### ISSUE-707: Servidor gRPC de Asistencias
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] Implementar `GetAsistenciaAlumno(alumnoId, materiaId) → [Asistencia]`
  - [ ] Implementar `GetEstadisticasAsistencia(materiaId) → Stats` (% asistencia, Presentes, Retardos, Ausentes)
  - [ ] Puerto gRPC: **50055**
- **Criterio de aceptación:** Los 2 métodos gRPC responden correctamente en el puerto 50055.

---

### ISSUE-708: Proceso de Confirmación de Lista por el Docente
- **Prioridad:** 🟡 Media
- **Tareas:**
  - [ ] `POST /sesiones/:id/confirmar` → el docente confirma la lista de asistencia de la sesión
  - [ ] `POST /sesiones/:id/solicitar-nueva` → el docente solicita repetir el pase de lista ante irregularidades (resetea la sesión)
- **Criterio de aceptación:** El docente puede confirmar o reiniciar el pase de lista.

---

## 📧 Epic 8: ms-notificaciones Notificaciones

### ISSUE-801: Configuración Base del Proyecto Django (ms-notificaciones) ✅
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [x] Inicializar proyecto Django en `/ms-notificaciones/`
  - [x] Dependencias: SMTP (Django), `grpcio`, `grpcio-tools`
  - [x] Configurar BD: `agm_notificaciones_db` (MySQL 8; historial de correos en tablas Django)
  - [x] Crear modelo `HistorialCorreo`: tipo, destinatario_email, asunto, enviado_en, exitoso, error_msg
  - [x] Configurar credenciales SMTP desde variables de entorno
- **Criterio de aceptación:** El MS levanta y puede enviar un correo de prueba.

---

### ISSUE-802: Correo de Bienvenida al Alumno ✅
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [x] `POST /notificaciones/bienvenida` → recibe alumno_id, materia_id, clave_acceso
  - [x] Consultar datos del alumno via gRPC a ms-alumnos y datos de la materia via gRPC a ms-periodos
  - [x] Enviar correo con clave de acceso e instrucciones
  - [x] Registrar el envío en `HistorialCorreo`
- **Criterio de aceptación:** El alumno recibe su clave de acceso por correo al ser importado.

---

### ISSUE-803: Notificación de Baja al Docente ✅
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [x] `POST /notificaciones/baja` → recibe alumno_id, docente_id, materia_id
  - [x] Consultar datos del alumno y del docente via gRPC
  - [x] Enviar correo al docente notificando la baja del alumno
  - [x] Registrar en `HistorialCorreo`
- **Criterio de aceptación:** El docente recibe notificación por correo cuando un alumno se da de baja.

---

### ISSUE-804: Notificación de Cierre de Materia a Alumnos ✅
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [x] `POST /notificaciones/cierre-materia` → recibe materia_id
  - [x] Obtener lista de alumnos de la materia via gRPC a ms-alumnos
  - [x] Enviar correo a cada alumno (ThreadPoolExecutor / `EMAIL_MAX_WORKERS`)
  - [x] Registrar cada envío en `HistorialCorreo`
- **Criterio de aceptación:** Todos los alumnos de la materia reciben correo de cierre.

---

### ISSUE-805: Correo de Reset de Contraseña ✅
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [x] `POST /notificaciones/reset-password` → recibe email, token, reset_url
  - [x] Enviar correo con enlace de restablecimiento
  - [x] Registrar en `HistorialCorreo`
- **Criterio de aceptación:** El usuario recibe el enlace de reset de contraseña por correo.

---

### ISSUE-806: Servidor gRPC de Notificaciones ✅
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [x] Implementar `SendBienvenida`, `SendBajaNotif`, `SendCierreMateria`, `SendResetPassword`
  - [x] Puerto gRPC: **50056** (`python -m grpc_server.server`)
- **Criterio de aceptación:** Los **4** métodos gRPC responden correctamente en el puerto 50056.

---

## 📄 Epic 9: ms-reportes Reportes & Estadísticas

### ISSUE-901: Configuración Base del Proyecto Django (ms-reportes)
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] Inicializar proyecto Django en `/ms-reportes/`
  - [ ] Dependencias: `openpyxl` (Excel), `reportlab` o `WeasyPrint` (PDF), `grpcio`, `grpcio-tools`
  - [ ] Configurar BD: `agm_reportes_db` (MySQL 8; opcional: tablas de caché / vistas para agregados pesados)
- **Criterio de aceptación:** El MS levanta y se conecta a su base de datos.

---

### ISSUE-902: Generación de Reporte de Calificaciones en Excel
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] `GET /reportes/calificaciones/:materiaId?formato=xls` → genera y descarga archivo Excel
  - [ ] Obtener datos del concentrado via gRPC a ms-calificaciones (`GetConcentrado`)
  - [ ] Obtener datos de alumnos via gRPC a ms-alumnos
  - [ ] Formato Excel: encabezado con nombre de materia, periodo, docente; columnas por actividad; promedio real; promedio redondeado
  - [ ] Usar `openpyxl` para generar el archivo; retornar con header `Content-Disposition: attachment; filename="calificaciones_NRC.xlsx"`
- **Criterio de aceptación:** Se descarga un Excel con el concentrado de calificaciones correctamente formateado.

---

### ISSUE-903: Generación de Reporte de Calificaciones en PDF
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] `GET /reportes/calificaciones/:materiaId?formato=pdf` → genera y descarga PDF
  - [ ] Mismos datos que el Excel pero en formato PDF con logo institucional (opcional) y pie de página
  - [ ] Usar `reportlab` o `WeasyPrint` para la generación
- **Criterio de aceptación:** Se descarga un PDF con el concentrado de calificaciones.

---

### ISSUE-904: Reporte de Concentrado de Asistencias
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] `GET /reportes/asistencias/:materiaId?formato=pdf|xls` → genera reporte de asistencias
  - [ ] Obtener datos via gRPC a ms-asistencias (`GetEstadisticasAsistencia`)
  - [ ] Incluir: alumno, total de clases, presentes, retardos, ausentes, % asistencia
- **Criterio de aceptación:** Se puede descargar el concentrado de asistencias en PDF y Excel.

---

### ISSUE-905: Estadísticas del Docente
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] `GET /estadisticas/docente/:id` → estadísticas históricas del docente por materia y periodo
  - [ ] Obtener materias del docente via gRPC a ms-periodos (`GetMateriasByDocente`)
  - [ ] Para cada materia/periodo: promedio grupal, % aprobación, % asistencia
  - [ ] Implementar comparativa si la misma materia fue impartida en múltiples periodos
- **Criterio de aceptación:** El docente puede ver el historial comparativo de sus materias.

---

### ISSUE-906: Estadísticas del Alumno
- **Prioridad:** 🟡 Media
- **Tareas:**
  - [ ] `GET /estadisticas/alumno/:id` → estadísticas del alumno en sus materias
  - [ ] Incluir: promedio actual, % asistencia, materias activas vs históricas
- **Criterio de aceptación:** El alumno puede ver sus estadísticas personales.

---

### ISSUE-907: Servidor gRPC de Reportes
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] Implementar `GenerateReport(params) → FileBytes`
  - [ ] Implementar `GetHistorialDocente(docenteId) → [StatsPeriodo]`
  - [ ] Puerto gRPC: **50057**
- **Criterio de aceptación:** Los 2 métodos gRPC responden correctamente en el puerto 50057.

---

## 🅰️ Epic 10: Frontend Angular 20 (Punto Extra)

> ⚠️ Esta epic es **opcional** y otorga +1 punto sobre la calificación final del semestre SOLO si está 100% completa, funcional, conectada al backend en producción y con diseño profesional.

### ISSUE-1001: Configuración Base del Proyecto Angular
- **Prioridad:** 🟡 Media (opcional)
- **Tareas:**
  - [ ] Crear proyecto Angular 20 con `ng new agm-frontend --routing --style=scss`
  - [ ] Instalar librería de componentes UI: `ng add @angular/material` (o PrimeNG/Taiga UI)
  - [ ] Configurar `src/environments/environment.ts` y `environment.prod.ts` con URLs de cada microservicio
  - [ ] Configurar Lazy Loading para módulos: `AdminModule`, `DocenteModule`, `AlumnoModule`
  - [ ] Implementar HTTP Interceptor para adjuntar JWT en todas las peticiones salientes
  - [ ] Implementar HTTP Interceptor para manejar errores 401 (redirigir al login)
  - [ ] Implementar Route Guards (`CanActivate`) por rol
  - [ ] Servicio `AuthService` con login, logout, almacenamiento de token y decodificación de JWT

---

### ISSUE-1002: Módulo de Autenticación
- **Prioridad:** 🟡 Media (opcional)
- **Tareas:**
  - [ ] Página de Login: formulario reactivo con validaciones (email válido, contraseña requerida), spinner durante carga, manejo de error 401
  - [ ] Página de Forgot Password: formulario con email
  - [ ] Página de Reset Password: formulario con token (desde URL param) y nueva contraseña
  - [ ] Redirección post-login según rol: Admin → `/admin`, Docente → `/docente`, Alumno → `/alumno`

---

### ISSUE-1003: Dashboard y Módulo del Administrador
- **Prioridad:** 🟡 Media (opcional)
- **Tareas:**
  - [ ] Dashboard Admin: periodo activo, fecha del sistema, accesos rápidos
  - [ ] Gestión de Periodos: tabla paginada, formulario de creación/edición, botón activar
  - [ ] Importación de Materias: uploader de PDF con barra de progreso y resumen de resultado
  - [ ] Importación de Docentes: uploader de PDF del directorio
  - [ ] Gestión de Docentes: tabla con búsqueda, botón reset de contraseña

---

### ISSUE-1004: Dashboard del Docente
- **Prioridad:** 🟡 Media (opcional)
- **Tareas:**
  - [ ] Dashboard con gráficas (Chart.js o ApexCharts): total materias, total alumnos, % asistencia del día
  - [ ] Tabla resumen de materias asignadas con estado

---

### ISSUE-1005: Módulo de Materias del Docente
- **Prioridad:** 🟡 Media (opcional)
- **Tareas:**
  - [ ] Lista de materias del periodo activo
  - [ ] Vista detalle de materia: alumnos, ponderaciones, actividades, concentrado
  - [ ] Importación de alumnos desde Excel con **vista previa** antes de confirmar
  - [ ] Configuración de ponderaciones con validación de suma=100%
  - [ ] CRUD de actividades por categoría
  - [ ] Entrada de calificaciones individual y por importación Excel
  - [ ] Botón cerrar materia con confirmación modal

---

### ISSUE-1006: Módulo de Asistencias QR del Docente
- **Prioridad:** 🟡 Media (opcional)
- **Tareas:**
  - [ ] Iniciar sesión de pase de lista para una materia
  - [ ] Temporizador regresivo de 10 minutos visible en pantalla
  - [ ] Escáner de QR usando cámara del dispositivo (`zxing-js` o `jsQR` con `MediaDevices API`)
  - [ ] Lista en tiempo real de alumnos escaneados con estado (Presente/Retardo)
  - [ ] Botón cerrar sesión anticipadamente
  - [ ] El módulo debe funcionar desde móvil (probar en Chrome mobile)

---

### ISSUE-1007: Módulo del Alumno
- **Prioridad:** 🟡 Media (opcional)
- **Tareas:**
  - [ ] Dashboard: bienvenida con nombre, matrícula, tipo formación, periodo activo
  - [ ] Lista de materias inscritas con NRC, docente, sección
  - [ ] Vista detalle de materia: actividades, calificaciones parciales, promedio actual
  - [ ] Botón "Solicitar Baja" con modal de confirmación (advertencia de irreversibilidad)
  - [ ] Estadísticas de asistencia por materia

---

### ISSUE-1008: Módulo de QR Dinámico del Alumno
- **Prioridad:** 🟡 Media (opcional)
- **Tareas:**
  - [ ] Pantalla de QR del alumno: genera y muestra el código QR con la librería `angularx-qrcode`
  - [ ] El QR se regenera automáticamente cada 30 segundos (llamada al backend para nuevo payload)
  - [ ] Mostrar temporizador visual indicando cuándo se regenerará el QR
  - [ ] La pantalla de QR debe funcionar y verse bien en dispositivos móviles

---

### ISSUE-1009: Reportes y Exportaciones en el Frontend
- **Prioridad:** 🟡 Media (opcional)
- **Tareas:**
  - [ ] Botón "Exportar Excel" en el concentrado de calificaciones (llama al endpoint de ms-reportes)
  - [ ] Botón "Exportar PDF" en el concentrado de calificaciones
  - [ ] Manejo de descarga de archivos binarios desde Angular con `blob`

---

### ISSUE-1010: Diseño Responsivo y UX General
- **Prioridad:** 🟡 Media (opcional)
- **Tareas:**
  - [ ] Aplicar diseño mobile-first con `breakpoints` de Angular Material
  - [ ] Implementar sidebar/navbar responsiva con menú hamburguesa en móvil
  - [ ] Tablas con paginación, búsqueda en tiempo real y ordenamiento por columnas
  - [ ] Todos los formularios con: mensajes de error inline, spinners de carga, toasts de éxito/error
  - [ ] Identidad visual consistente: paleta de colores, tipografía y iconografía unificadas
  - [ ] **NO usar Bootstrap sin personalización. NO usar tablas sin estilo.**
- **Criterio de aceptación:** El módulo de QR funciona en móvil. Todos los formularios tienen validación visual.

---

### ISSUE-1011: Despliegue del Frontend
- **Prioridad:** 🟡 Media (opcional)
- **Tareas:**
  - [ ] Build de producción: `ng build --configuration production`
  - [ ] Desplegar en plataforma estática: Vercel, Netlify o GitHub Pages
  - [ ] Configurar `environment.prod.ts` con las URLs reales de producción de cada MS
  - [ ] Verificar que funcione con HTTPS y no tenga errores de CORS en producción
- **Criterio de aceptación:** El frontend está accesible públicamente via HTTPS y conectado al backend en producción.

---

### ISSUE-1012: Historial del Docente con Estadísticas Comparativas
- **Prioridad:** 🟡 Media (opcional)
- **Tareas:**
  - [ ] Vista de historial académico del docente: materias impartidas por periodo
  - [ ] Gráfica comparativa si la misma materia se impartió en múltiples periodos
  - [ ] Indicadores visuales para periodos inactivos (ej. badge "Finalizado")

---

## 📚 Epic 11: Documentación y Entregables

### ISSUE-1101: README Principal del Repositorio
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] Descripción del proyecto (1-2 párrafos)
  - [ ] Tabla de integrantes con nombre y rol (líder, dev MS-X, DBA, DevOps, QA)
  - [ ] Stack tecnológico completo (tabla MS → tecnología → BD)
  - [ ] Prerrequisitos: Docker, Docker Compose, versiones requeridas
  - [ ] Instrucciones de instalación local paso a paso:
    1. Clonar repositorio
    2. Copiar `.env.example` a `.env` en cada MS
    3. Completar variables de entorno
    4. `docker compose up --build` (o `docker-compose up --build`)
  - [ ] URLs de producción de cada microservicio (tabla)
  - [ ] URL del video demostrativo en YouTube
  - [ ] Estructura del repositorio explicada
- **Criterio de aceptación:** Un desarrollador externo puede clonar el repositorio y levantarlo localmente siguiendo solo el README.

---

### ISSUE-1102: Manual de Usuario
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] Portada: nombre del proyecto, equipo, materia, fecha
  - [ ] Índice con hipervínculos a cada sección
  - [ ] Introducción y propósito del sistema
  - [ ] Sección de acceso: cómo entrar al sistema (frontend o Swagger/Postman si no hay frontend)
  - [ ] **Sección Administrador**: paso a paso con capturas de cada funcionalidad (gestión periodos, importación PDF, gestión docentes)
  - [ ] **Sección Docente**: paso a paso con capturas (ponderaciones, importar alumnos, calificaciones, QR, exportar reporte)
  - [ ] **Sección Alumno**: paso a paso con capturas (consultar calificaciones, QR, solicitar baja)
  - [ ] Diseño profesional: portada estilizada, numeración de páginas, encabezados/pies de página
- **Criterio de aceptación:** El manual tiene sección por cada rol con capturas reales del sistema en producción.

---

### ISSUE-1103: Manual Técnico
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] Diagrama de arquitectura de microservicios (con herramienta como draw.io, Lucidchart o Mermaid):
    - Mostrar los 7 MS con sus puertos REST y gRPC
    - Mostrar las bases de datos individuales
    - Flechas indicando comunicación gRPC entre servicios
    - Flecha del cliente hacia el API Gateway
  - [ ] Stack tecnológico con justificación por MS
  - [ ] Modelo de datos: diagrama ER o de colecciones + diccionario de datos por cada MS
  - [ ] Contratos gRPC: descripción de cada `.proto` con sus servicios y mensajes
  - [ ] Documentación de la API REST: para cada endpoint de cada MS → método, URL, parámetros, body, response, códigos de error
  - [ ] Colección Postman exportada (`.json`) o archivo `openapi.yaml` en el repositorio
  - [ ] Guía de instalación local (puede referenciar el README)
  - [ ] Guía de despliegue en producción (paso a paso para Railway/Render)
- **Criterio de aceptación:** Un desarrollador externo puede entender la arquitectura y los contratos del sistema solo leyendo el Manual Técnico.

---

### ISSUE-1104: Colección Postman / OpenAPI
- **Prioridad:** 🟠 Alta
- **Tareas:**
  - [ ] Crear colección Postman con todos los endpoints de los 7 MS organizados por carpeta
  - [ ] Configurar variables de entorno en Postman: `base_url`, `access_token`
  - [ ] Incluir ejemplos de request y response en cada endpoint
  - [ ] Exportar colección como `postman_collection.json` y subir al repositorio
  - [ ] Alternativamente: configurar `drf-spectacular` en Django para generar OpenAPI automáticamente
- **Criterio de aceptación:** Cualquier evaluador puede importar la colección y probar todos los endpoints.

---

### ISSUE-1105: Video Demostrativo (YouTube)
- **Prioridad:** 🔴 Crítica
- **Tareas:**
  - [ ] Duración: entre 10 y 20 minutos
  - [ ] Estructura del video:
    - [ ] (0-2 min) Presentación del equipo, nombres y roles
    - [ ] (2-4 min) Arquitectura: repositorio en GitHub, URLs en producción, estructura de carpetas
    - [ ] (4-7 min) Flujo completo del Administrador: login, crear periodo, importar PDF materias, importar PDF docentes
    - [ ] (7-12 min) Flujo completo del Docente: importar alumnos Excel, configurar ponderaciones, registrar calificaciones, pase de lista QR, cerrar materia, exportar reporte
    - [ ] (12-15 min) Flujo completo del Alumno: login con clave única, ver calificaciones, generar QR, solicitar baja
    - [ ] (15-17 min) Demostración de notificaciones por correo en funcionamiento real
    - [ ] (17-20 min) Si aplica: demostración del frontend en móvil
  - [ ] Subir a YouTube (puede ser privado con enlace compartible)
  - [ ] Agregar URL del video al README
- **Criterio de aceptación:** El video existe en YouTube, dura entre 10-20 min y muestra todos los flujos en producción.

---

### ISSUE-1106: Control de Calidad Pre-Entrega (Checklist)
- **Prioridad:** 🔴 Crítica
- **Descripción:** Verificación final antes de la presentación.
- **Tareas:**
  - [ ] Verificar que los 7 MS están desplegados y accesibles por HTTPS
  - [ ] Verificar que `docker compose up --build` (o `docker-compose up --build`) funciona en una máquina limpia
  - [ ] Verificar que el repositorio tiene **más de 20 commits** con historial distribuido durante el semestre
  - [ ] Verificar que NO hay credenciales hardcodeadas en el código (ni contraseñas, ni API keys, ni secrets)
  - [ ] Verificar que todos los `.env.example` están presentes
  - [ ] Verificar que la carpeta `/proto` tiene todos los archivos `.proto`
  - [ ] Verificar que al menos 3 pares de MS se comunican via gRPC funcionalmente
  - [ ] Verificar que la suma de ponderaciones funciona correctamente (no permite ≠ 100%)
  - [ ] Verificar que el anti-replay del QR funciona (el mismo QR no puede registrarse dos veces)
  - [ ] Verificar que la regla de redondeo es correcta (7.5 → 8, 7.4 → 7)
  - [ ] Verificar que la baja de materia es irreversible y notifica al docente
  - [ ] Verificar que el Manual Técnico, Manual de Usuario y video están listos
  - [ ] Verificar que la colección Postman está en el repositorio
- **Criterio de aceptación:** Todos los ítems del checklist están marcados antes de la presentación.

---

## 📊 Resumen de Issues por Prioridad

| Prioridad | Cantidad | Descripción |
|-----------|----------|-------------|
| 🔴 Crítica | ~40 | Sin estas issues el proyecto no pasa evaluación |
| 🟠 Alta | ~28 | Necesarias para calificación completa |
| 🟡 Media | ~15 | Punto extra o funcionalidades secundarias |

## 📊 Resumen por Criterio de Evaluación

| Criterio (peso) | Issues clave |
|-----------------|-------------|
| Arquitectura MS real (30%) | ISSUE-101, 102, 103, 301/401/501/601/701/801/901 |
| Comunicación gRPC (20%) | ISSUE-201, 202, 203, 204, 305, 405, 507, 609, 707, 806, 907 |
| Funcionalidad backend (25%) | ISSUE-302 a 308, 402 a 408, 502 a 509, 602 a 609, 702 a 708, 802 a 806, 902 a 907 |
| Despliegue en producción (10%) | ISSUE-106, 104, 105 |
| Calidad del código/repo (8%) | ISSUE-101, 104, 1101 |
| Documentación técnica (7%) | ISSUE-1101, 1102, 1103, 1104, 1105 |
| Punto extra frontend (+1) | ISSUE-1001 a 1012 |
