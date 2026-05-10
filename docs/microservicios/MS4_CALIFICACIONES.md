# 📊 MS-4: Calificaciones & Ponderaciones — Especificación para IA

> **Lee primero**: `docs/CONTEXTO_GLOBAL_PROYECTO.md`

---

## Identidad

| Campo | Valor |
|-------|-------|
| **Carpeta** | `/ms-calificaciones/` |
| **Puerto REST** | 8004 |
| **Puerto gRPC** | 50054 |
| **BD** | MySQL – `agm_calificaciones_db` |
| **Responsabilidad** | Ponderaciones (criterios 100%), actividades, calificaciones individuales/masivas, promedios ponderados, cierre de materia |

## Dependencias extras
`openpyxl>=3.1` (importar calificaciones Excel)

## Modelos

### `Ponderacion`
- `materia_id` (IntegerField) — FK lógica a MS-2
- `nombre_categoria` (CharField 100) — Ej: "Exámenes", "Tareas"
- `porcentaje` (DecimalField 5,2) — Ej: 40.00
- **Constraint**: La suma de porcentajes por materia_id DEBE ser exactamente 100.00

### `Actividad`
- `ponderacion` (FK → Ponderacion)
- `nombre` (CharField 255) — Ej: "Examen Parcial 1"
- `descripcion` (TextField, blank)
- `fecha` (DateField, null)

### `Calificacion`
- `actividad` (FK → Actividad)
- `alumno_id` (IntegerField) — FK lógica a MS-3
- `calificacion` (DecimalField 4,2) — Rango 0.00 a 10.00
- `fecha_asignacion` (DateTimeField auto_now)
- **unique_together**: `['actividad', 'alumno_id']`

### `EstadoMateria`
- `materia_id` (IntegerField, unique)
- `cerrada` (BooleanField, default=False)
- `lista_impresa` (BooleanField, default=False)

## Endpoints REST

### Ponderaciones
- `GET /ponderaciones/:materiaId` — obtener ponderaciones (auth: docente de la materia o admin)
- `POST /ponderaciones/:materiaId` — crear ponderaciones (lista de {nombre_categoria, porcentaje}). **Validar suma=100%**
- `PUT /ponderaciones/:materiaId` — actualizar. **Validar suma=100%**

### Actividades
- `POST /actividades` — crear actividad bajo una ponderación
- `GET /actividades?materia=:id` — listar actividades organizadas por categoría
- `PUT /actividades/:id` — editar
- `DELETE /actividades/:id` — eliminar (solo si no tiene calificaciones)

### Calificaciones
- `POST /calificaciones` — asignar calificación individual `{actividad_id, alumno_id, calificacion}`
  - Validar: alumno existe en materia (gRPC a MS-3 `IsAlumnoEnMateria`)
  - Validar: 0 ≤ calificación ≤ 10
  - Validar: materia no tiene `lista_impresa=True`
- `PUT /calificaciones/:id` — actualizar (si no está impresa la lista)
- `POST /calificaciones/importar` — importar desde Excel (matrícula, actividad_id, calificación)
- `GET /concentrado/:materiaId` — tabla completa:
  - Alumnos (gRPC a MS-3), calificaciones por actividad, promedio real, promedio redondeado

### Cierre de materia
- `POST /materias/:id/cerrar` — marca cerrada + gRPC a MS-6 `SendCierreMateria`
- `POST /materias/:id/imprimir-lista` — marca `lista_impresa=True`. Después: NO más cambios en calificaciones

## Cálculo de Promedio Ponderado (CRÍTICO)
```python
def calcular_promedio(alumno_id, materia_id):
    ponderaciones = Ponderacion.objects.filter(materia_id=materia_id)
    promedio_total = 0
    for pond in ponderaciones:
        actividades = pond.actividades.all()
        califs = Calificacion.objects.filter(actividad__in=actividades, alumno_id=alumno_id)
        if califs.exists():
            promedio_categoria = califs.aggregate(Avg('calificacion'))['calificacion__avg']
        else:
            promedio_categoria = 0
        promedio_total += promedio_categoria * (pond.porcentaje / 100)
    return promedio_total

def redondear_institucional(promedio):
    parte_decimal = promedio - int(promedio)
    if parte_decimal >= 0.5:
        return int(promedio) + 1  # 7.5 → 8
    else:
        return int(promedio)      # 7.4 → 7
```

## Servidor gRPC (Puerto 50054)
```protobuf
syntax = "proto3";
package calificaciones;

service CalificacionesService {
  rpc GetConcentrado(GetConcentradoRequest) returns (ConcentradoResponse);
  rpc GetPromedioAlumno(GetPromedioAlumnoRequest) returns (PromedioResponse);
  rpc GetEstadisticasMateria(GetEstadisticasMateriaRequest) returns (EstadisticasResponse);
}
// Messages: materia_id, alumno_id → listas de calificaciones, promedios, stats (aprobados/reprobados/promedio_grupal)
```

## Clientes gRPC
| Destino | Método | Cuándo |
|---------|--------|--------|
| MS-1 | ValidateToken | Cada request |
| MS-3 | GetAlumnosByMateria, IsAlumnoEnMateria | Concentrado, validar calificación |
| MS-2 | GetMateriaById | Validar que el docente es dueño de la materia |
| MS-6 | SendCierreMateria | Al cerrar materia |

## Reglas Críticas
1. Suma de ponderaciones = exactamente 100% (400 si no)
2. Calificaciones: 0–10, máximo 2 decimales
3. Redondeo: ≥0.5 → arriba, <0.5 → abajo
4. `lista_impresa=True` → BLOQUEA toda edición de calificaciones
5. Solo el docente de la materia puede gestionar calificaciones
