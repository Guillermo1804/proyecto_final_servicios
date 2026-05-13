# Plan de acción — Epic 1: Infraestructura y DevOps

**Desarrollador:** Makinohara  
**Alcance:** `docs/backlog_AGM_completo.md` — Epic 1 (ISSUE-101 … ISSUE-107)  
**Marco normativo:** `docs/Proyecto_Final_SW_AGM.md` (§4.2 Tecnologías, §5.4.2 BD por MS, §5.4.5 API REST, §5.4.6 Despliegue, §6.4 Repositorio) y `docs/CONTEXTO_GLOBAL_PROYECTO.md`

---

## 1. Objetivo del plan

Entregar una base **reproducible, segura y desplegable** para los siete microservicios AGM: monorepo con convenciones claras, contenedores independientes, orquestación local con un solo comando, variables de entorno documentadas, CORS acotado, gateway Nginx y criterios de publicación en nube con HTTPS — sin implementar lógica de negocio de MS-1…MS-7 (eso corresponde a otros issues), pero **garantizando** que cualquier MS que se integre pueda enchufarse al mismo patrón.

---

## 2. Resultados medibles (definición de “terminado”)

| # | Resultado | Evidencia |
|---|-----------|-----------|
| R1 | Estructura de carpetas oficial | Existen `/ms-auth`, `/ms-periodos`, `/ms-alumnos`, `/ms-calificaciones`, `/ms-asistencias`, `/ms-notificaciones`, `/ms-reportes`, `/proto` (y `/frontend` si aplica punto extra) |
| R2 | Cada MS construye imagen Docker de forma aislada | `docker build` exitoso en cada carpeta `ms-*` |
| R3 | Sistema completo en local | `docker compose up --build` (o `docker-compose`) levanta 7 MS + 7 MySQL + Redis (MS-5) sin errores de arranque |
| R4 | Sin secretos en Git | `.env` ignorado; solo `.env.example` por MS con placeholders |
| R5 | Producción | Las 7 URLs HTTPS documentadas en README (ISSUE-1101 lo consume el equipo; este plan prepara la base) |
| R6 | Gateway | Una URL base enruta `/auth/*`, `/periodos/*`, … según `CONTEXTO_GLOBAL_PROYECTO.md` |

---

## 3. Dependencias y coordinación

- **Epic 2 (gRPC):** los Dockerfiles deben exponer REST + gRPC; los puertos 50051–50057 deben estar reservados en `docker-compose` y documentados. Si Epic 2 aún no genera código, igual se fijan **variables de entorno** y **puertos** para no romper después.
- **Otros devs:** cada MS debe incluir `requirements.txt`, `entrypoint.sh` coherente y healthcheck REST mínimo (`/` o `/health`) acordado con el equipo.
- **Orden sugerido:** completar **101 → 104 → 102 → 103** antes de **105–107**; el despliegue cloud (**106**) puede ir en paralelo una vez **103** sea estable en máquina limpia.

---

## 4. Fases de ejecución (orden estricto recomendado)

### Fase A — ISSUE-101: Repositorio monorepo

**Meta:** GitHub público, ramas `main` / `develop`, estructura y `.gitignore`.

| Paso | Acción | Verificación |
|------|--------|----------------|
| A1 | Crear/validar repo público y ramas | Remoto accesible; `main` protegida con PR si aplica política del equipo |
| A2 | Carpetas raíz según backlog | `ls` coincide con tabla del ISSUE-101 |
| A3 | `.gitignore` global | `git status` no muestra `.env`, `__pycache__`, `*.pyc`, `node_modules` |
| A4 | README inicial | Nombre del proyecto + lista de integrantes (se ampliará en Epic 11) |

**Errores frecuentes:** mezclar código de varios MS en una sola carpeta; olvidar `/proto` en la raíz.

---

### Fase B — ISSUE-104: `.env.example` por microservicio (antes de Docker final)

**Meta:** Contrato de configuración por MS para que Compose y cloud no adivinen nombres.

| Paso | Acción | Verificación |
|------|--------|----------------|
| B1 | Plantilla mínima por MS | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_CHARSET=utf8mb4`, `REST_PORT`, `GRPC_PORT`, `ALLOWED_HOSTS`, `SECRET_KEY` (placeholder) |
| B2 | MS-5 incluye Redis | Variables `REDIS_URL` o host/puerto según implementación del MS-5 |
| B3 | MS con clientes gRPC | `MS_*_GRPC_HOST` / puertos documentados hacia otros servicios (valores ejemplo con nombres de servicio Docker) |
| B4 | MS-6 SMTP | `EMAIL_*` según `MS6_NOTIFICACIONES.md` |

**Errores frecuentes:** usar `localhost` como `DB_HOST` dentro de Compose (debe ser nombre del servicio, p. ej. `db-auth`).

---

### Fase C — ISSUE-102: Dockerfile por microservicio

**Meta:** Imagen reproducible por MS, capas cacheables, puertos REST + gRPC.

| Paso | Acción | Verificación |
|------|--------|----------------|
| C1 | Base `python:3.12-slim` (o la acordada) | Misma línea base en los 7 MS |
| C2 | Orden de capas | Copiar e instalar `requirements.txt` **antes** del código fuente |
| C3 | Exponer puertos | `EXPOSE` REST (8001–8007) y gRPC (50051–50057) según MS |
| C4 | Comando de arranque | Gunicorn + proceso gRPC si el entrypoint lo lanza (coordinar con Epic 2) |
| C5 | `docker build -t agm-ms-auth ./ms-auth` (y análogos) | Build sin error en CI o local |

**Errores frecuentes:** no fijar versión de imagen base; copiar todo el repo dentro de la imagen de un solo MS.

---

### Fase D — ISSUE-103: `docker-compose.yml` unificado

**Meta:** Un comando levanta el ecosistema.

| Paso | Acción | Verificación |
|------|--------|----------------|
| D1 | Un servicio `db-*` por MS con MySQL 8 | Charset `utf8mb4`; volumen persistente por BD |
| D2 | Servicio `redis` solo para MS-5 | Red interna bridge |
| D3 | Nombres de host | Cada `ms-*` usa `DB_HOST` = nombre del contenedor DB correspondiente |
| D4 | `depends_on` + **healthcheck** en MySQL | MS no arranca migraciones hasta BD lista |
| D5 | `env_file` por servicio | Apunta a `.env` local (no versionado) |
| D6 | Red única | Todos los contenedores se resuelven por DNS interno |
| D7 | Prueba en máquina limpia | Clonar repo fresco, copiar `.env.example` → `.env`, `docker compose up --build` |

**Errores frecuentes:** un solo contenedor MySQL con siete bases sin aislamiento del enunciado (el proyecto exige **instancia o esquema separado por MS**; en Docker lo habitual es **un contenedor MySQL por MS** como indica el backlog).

---

### Fase E — ISSUE-105: CORS

**Meta:** CORS acorde a `Proyecto_Final_SW_AGM.md` §5.4.5 (orígenes autorizados en producción).

| Paso | Acción | Verificación |
|------|--------|----------------|
| E1 | `django-cors-headers` en cada MS Django | Misma política documentada |
| E2 | Desarrollo vs producción | `CORS_ALLOWED_ORIGINS` explícito en prod; prohibido `CORS_ALLOW_ALL_ORIGINS=True` en entrega |
| E3 | Preflight | `OPTIONS` responde 200 en rutas API |

---

### Fase F — ISSUE-107: API Gateway (Nginx)

**Meta:** Punto de entrada único alineado con `CONTEXTO_GLOBAL_PROYECTO.md` §2.

| Paso | Acción | Verificación |
|------|--------|----------------|
| F1 | `docker/nginx/default.conf` (o ruta acordada) | Rutas `/auth/*` → 8001, `/periodos/*` → 8002, … |
| F2 | Incluir gateway en Compose | Servicio `nginx` depende de MS o usa red compartida |
| F3 | Headers | `proxy_set_header Host`, `X-Forwarded-Proto` para HTTPS detrás del proxy |
| F4 | CORS | Decidir si CORS vive en Nginx o en cada MS (evitar duplicidad conflictiva) |

---

### Fase G — ISSUE-106: Despliegue en nube

**Meta:** Siete URLs HTTPS públicas al momento de presentación.

| Paso | Acción | Verificación |
|------|--------|----------------|
| G1 | Elegir plataforma (Railway / Render / Fly.io) | Criterio: MySQL 8 gestionado o contenedor estable |
| G2 | Un servicio web por MS | Variables de entorno solo en panel cloud |
| G3 | Bases de datos | Una BD lógica por MS (`agm_*_db`) |
| G4 | Smoke test remoto | `curl -I https://...` 200/401 esperado en health o login |
| G5 | Documentar URLs | Tabla en README |

**Errores frecuentes:** exponer credenciales en logs; desplegar solo un subconjunto de MS (evaluación §7.2).

---

## 5. Matriz de trazabilidad backlog ↔ riesgo

| Issue | Riesgo principal | Mitigación |
|-------|------------------|------------|
| 101 | Estructura inconsistente | Checklist de carpetas en PR template |
| 102 | Imágenes pesadas o lentas | Multi-stage si crece el contexto; `.dockerignore` por MS |
| 103 | Condiciones de carrera en BD | `healthcheck` + `depends_on` con condición healthy si Compose lo soporta |
| 104 | Fuga de secretos | Revisión `git grep -i password` antes de push |
| 105 | CORS abierto | Revisión de prod en checklist ISSUE-1106 |
| 106 | Costos / sleep en free tier | Documentar limitaciones; health pings si aplica |
| 107 | Rutas mal enrutadas | Tabla de rutas en README + prueba Postman vía gateway |

---

## 6. Checklist final (calidad “a prueba de errores”)

- [ ] `docker compose up --build` desde cero (sin volúmenes previos) completado al menos una vez grabado o documentado.
- [ ] Ningún `.env` en el historial reciente (`git log --all --full-history -- .env`).
- [ ] Puertos 8001–8007 y 50051–50057 sin colisiones en documentación.
- [ ] Gateway: una URL base prueba los 7 prefijos (aunque la respuesta sea 401 sin token).
- [ ] README o wiki interna: “cómo copiar envs” y “cómo levantar”.
- [ ] Alineación con **ISSUE-1106** (pre-entrega): Compose funcional, sin credenciales hardcodeadas.

---

## 7. Referencias rápidas

- Backlog: ISSUE-101 … ISSUE-107  
- Proyecto final: §4.2, §5.4.2, §5.4.5, §5.4.6, §6.4  
- Contexto: secciones 2 (diagrama gateway), 4 (tabla de puertos), 6 (patrones comunes)
