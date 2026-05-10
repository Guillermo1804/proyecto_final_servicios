# 📄 MS-7: Reportes & Estadísticas — Especificación para IA

> **Lee primero**: `docs/CONTEXTO_GLOBAL_PROYECTO.md`

---

## Identidad

| Campo | Valor |
|-------|-------|
| **Carpeta** | `/ms-reportes/` |
| **Puerto REST** | 8007 |
| **Puerto gRPC** | 50057 |
| **BD** | MySQL – `agm_reportes_db` |
| **Responsabilidad** | Generación de reportes Excel/PDF de calificaciones y asistencias, estadísticas históricas |

## Dependencias extras
```
openpyxl>=3.1
reportlab>=4.1
```

## Modelos
Este MS tiene modelos mínimos propios (puede cachear estadísticas). La mayoría de datos los obtiene via gRPC.

### `ReporteGenerado` (opcional, para caché/historial)
- `tipo` (CharField: 'calificaciones', 'asistencias')
- `formato` (CharField: 'pdf', 'xlsx')
- `materia_id` (IntegerField)
- `generado_por` (IntegerField — user_id)
- `archivo` (FileField o BinaryField)
- `generado_en` (DateTimeField auto_now_add)

## Endpoints REST

### Reportes de Calificaciones
- `GET /reportes/calificaciones/:materiaId?formato=xlsx` — Genera y descarga Excel
  - gRPC a MS-4: `GetConcentrado(materiaId)` → datos completos
  - gRPC a MS-3: `GetAlumnosByMateria` → nombres y matrículas
  - gRPC a MS-2: `GetMateriaById` → nombre materia, periodo, docente
  - Generar Excel con `openpyxl`: encabezado, columnas por actividad, promedio real, promedio redondeado
  - Response: archivo con `Content-Disposition: attachment; filename="calificaciones_{NRC}.xlsx"`

- `GET /reportes/calificaciones/:materiaId?formato=pdf` — Lo mismo pero en PDF con `reportlab`

### Reportes de Asistencias
- `GET /reportes/asistencias/:materiaId?formato=xlsx|pdf`
  - gRPC a MS-5: `GetEstadisticasAsistencia`
  - gRPC a MS-3: `GetAlumnosByMateria`
  - Tabla: alumno, total clases, presentes, retardos, ausentes, % asistencia

### Estadísticas
- `GET /estadisticas/docente/:id` — historial del docente por periodo
  - gRPC a MS-2: `GetMateriasByDocente`
  - gRPC a MS-4: `GetEstadisticasMateria` por cada materia
  - Comparativa entre periodos si la misma materia fue impartida múltiples veces

- `GET /estadisticas/alumno/:id` — stats del alumno
  - gRPC a MS-4: `GetPromedioAlumno` por cada materia
  - gRPC a MS-5: `GetAsistenciaAlumno` por cada materia

## Servidor gRPC (Puerto 50057)
```protobuf
syntax = "proto3";
package reportes;
service ReportesService {
  rpc GenerateReport(GenerateReportRequest) returns (ReportResponse);
  rpc GetHistorialDocente(GetHistorialDocenteRequest) returns (HistorialResponse);
}
// GenerateReport: tipo, materia_id, formato → bytes del archivo
// GetHistorialDocente: docente_id → lista de {periodo, materia, promedio_grupal, aprobados, reprobados}
```

## Clientes gRPC
| Destino | Método | Cuándo |
|---------|--------|--------|
| MS-1 | ValidateToken | Cada request |
| MS-2 | GetMateriaById, GetMateriasByDocente | Datos de materia para reportes |
| MS-3 | GetAlumnosByMateria | Nombres/matrículas para reportes |
| MS-4 | GetConcentrado, GetEstadisticasMateria, GetPromedioAlumno | Datos de calificaciones |
| MS-5 | GetEstadisticasAsistencia, GetAsistenciaAlumno | Datos de asistencias |

## Reglas Críticas
1. Los reportes se generan en TIEMPO REAL (no precalculados)
2. Los archivos se devuelven como respuesta HTTP directa (streaming)
3. Solo docentes de la materia o admin pueden generar reportes
4. El PDF debe tener formato institucional: encabezado, tabla, pie de página
