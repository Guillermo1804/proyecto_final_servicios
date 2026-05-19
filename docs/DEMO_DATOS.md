# Datos demo AGM — credenciales y qué ver en cada pantalla

Cargar datos (stack Docker arriba):

```powershell
.\scripts\seed-demo.ps1
```

Idempotente: puedes ejecutarlo varias veces.

Si el API devuelve **502** tras `docker compose up` o rebuild de MS, reinicia el gateway: `docker compose restart nginx` (el script `seed-demo.ps1` ya lo hace al final).

---

## Credenciales

| Rol | Email | Contraseña |
|-----|--------|------------|
| Admin | `admin@agm.buap.mx` | `admin123` |
| Docente | `docente.demo@agm.buap.mx` | `Docente123!` |
| Alumno (principal) | `alumno.demo@agm.buap.mx` | `Alumno123!` |
| Alumno 2 | `alumno2.demo@agm.buap.mx` | `Alumno123!` |
| Alumno 3 | `alumno3.demo@agm.buap.mx` | `Alumno123!` |

---

## Datos creados

### MS-2 — Periodos y materias
- Periodo activo: **2026-1 Primavera Demo**
- Materias (docente titular = usuario docente):
  1. Programación Web (NRC 12345)
  2. Bases de Datos (NRC 12346)
  3. Ingeniería de Software (NRC 12347)

### MS-3 — Alumnos
- 6 alumnos (matrículas 202600001–202600006)
- Inscripciones: todos en Programación Web; 3 con login en más materias; Ana en las 3 materias

### MS-4 — Calificaciones
- Plan 30/30/40 + 4 actividades por materia
- Notas variadas (aprobadas y en riesgo) para reportes y concentrado

### MS-5 — Asistencias
- 3 sesiones cerradas/confirmadas en Programación Web con registros presente/retardo/ausente

---

## Qué probar por rol

### Admin (`/admin`)
| Pantalla | Qué deberías ver |
|----------|------------------|
| Dashboard | Conteos periodo/materias/docentes |
| Periodos | Periodo activo 2026-1 + acciones |
| Materias | 3 materias + crear/editar |
| Docentes | Docente demo + import PDF |

### Docente (`/docente`)
| Pantalla | Qué deberías ver |
|----------|------------------|
| Dashboard | Stats MS-7 |
| Materias | 3 materias, alumnos y % asistencia |
| Detalle materia | Lista alumnos, % asistencia, plan evaluación |
| Calificaciones | Concentrado con columnas y notas |
| Asistencias | Iniciar sesión / escanear (alumno QR) |
| Reportes | Gráficas y descarga PDF/Excel |
| Rendimiento | Riesgo desde concentrado |

### Alumno (`/alumno`)
| Pantalla | Qué deberías ver |
|----------|------------------|
| Dashboard | Promedio y materias MS-7 |
| Horario | Materias inscritas |
| Notas | Calificaciones MS-4 + historial por periodo |
| QR | Token MS-5 (con sesión activa docente) |
| Perfil | Datos MS-1 + MS-3 |

---

## Flujo E2E recomendado (asistencias)

1. Login **docente** → Asistencias → iniciar pase de lista (Programación Web).
2. Login **alumno.demo** → QR → mostrar código.
3. Docente → escanear QR → registro en lista.
4. Docente → confirmar lista.

---

## Comandos manuales por MS

```powershell
.\scripts\seed-demo.ps1
```

Si prefieres paso a paso, usa los `SEED_*` que imprime cada comando (los IDs de materias/alumnos suelen ser `2,3,4` y `1,6,7,8,9,10` en una BD ya usada).
