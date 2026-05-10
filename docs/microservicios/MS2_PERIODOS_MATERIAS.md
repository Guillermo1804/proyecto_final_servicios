# 📅 MS-2: Periodos & Materias — Especificación Completa para IA

> **Lee primero**: `docs/CONTEXTO_GLOBAL_PROYECTO.md` para entender la arquitectura general.

---

## Identidad del Microservicio

| Campo | Valor |
|-------|-------|
| **Nombre** | ms-periodos |
| **Carpeta** | `/ms-periodos/` |
| **Puerto REST** | 8002 |
| **Puerto gRPC** | 50052 |
| **Base de datos** | MySQL – `agm_periodos_db` |
| **Responsabilidad** | CRUD de periodos académicos, importación de materias desde PDF, gestión del catálogo de materias, validación de periodo único activo |

---

## Dependencias Python (`requirements.txt`)

```
Django>=5.0,<6.0
djangorestframework>=3.15
django-cors-headers>=4.3
mysqlclient>=2.2
grpcio>=1.60
grpcio-tools>=1.60
python-decouple>=3.8
gunicorn>=21.2
pdfplumber>=0.10
```

---

## Modelos de Base de Datos

### `Periodo`
```python
class Periodo(Model):
    nombre = CharField(max_length=100)                    # Ej: "Primavera 2026"
    fecha_inicio = DateField()
    fecha_fin = DateField()
    plan_estudios = CharField(max_length=100)              # Ej: "Plan 2021"
    activo = BooleanField(default=False)                   # Solo 1 puede ser True a la vez
    fecha_creacion = DateTimeField(auto_now_add=True)
    fecha_actualizacion = DateTimeField(auto_now=True)

    class Meta:
        # Constraint: si activo=True, debe ser único
        constraints = [
            UniqueConstraint(
                fields=['activo'],
                condition=Q(activo=True),
                name='unique_periodo_activo'
            )
        ]
```

### `Materia`
```python
class Materia(Model):
    periodo = ForeignKey(Periodo, on_delete=CASCADE, related_name='materias')
    nrc = CharField(max_length=20)                         # Código único de la materia en el periodo
    nombre = CharField(max_length=255)                     # Ej: "Servicios Web"
    seccion = CharField(max_length=10)                     # Ej: "001"
    clave = CharField(max_length=20)                       # Ej: "COMP-456"
    docente_nombre = CharField(max_length=255)             # Nombre del docente (texto)
    docente_id = IntegerField(null=True, blank=True)       # ID en MS-3 (se llena después)
    horario = CharField(max_length=255)                    # Ej: "Lun-Mie 10:00-12:00"
    fecha_creacion = DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['periodo', 'nrc']               # NRC único por periodo
```

---

## Endpoints REST

### Periodos

#### `GET /periodos`
- **Auth**: JWT (cualquier rol)
- **Query params**: `?page=1&limit=10`
- **Response 200**: Lista paginada de periodos con info básica

#### `POST /periodos`
- **Auth**: JWT + rol `admin`
- **Body**:
  ```json
  {
    "nombre": "Primavera 2026",
    "fecha_inicio": "2026-02-01",
    "fecha_fin": "2026-06-30",
    "plan_estudios": "Plan 2021"
  }
  ```
- **Validaciones**:
  - `fecha_inicio < fecha_fin`
  - Nombre no vacío
- **Response 201**: Periodo creado

#### `PUT /periodos/:id`
- **Auth**: JWT + rol `admin`
- **Body**: Campos a actualizar
- **Response 200**: Periodo actualizado

#### `DELETE /periodos/:id`
- **Auth**: JWT + rol `admin`
- **Validación**: Solo si no tiene materias asociadas
- **Response 200**: Periodo eliminado
- **Response 400**: "No se puede eliminar un periodo con materias asociadas"

#### `POST /periodos/:id/activar`
- **Auth**: JWT + rol `admin`
- **Lógica CRÍTICA**:
  1. Desactivar CUALQUIER otro periodo que tenga `activo=True`
  2. Activar el periodo indicado
  3. Esto debe ser atómico (transacción)
- **Response 200**: `{ "message": "Periodo activado exitosamente" }`

#### `GET /periodos/activo`
- **Auth**: JWT (cualquier rol) — o incluso público
- **Response 200**: Datos del periodo actualmente activo
- **Response 404**: No hay periodo activo

### Materias

#### `GET /materias`
- **Auth**: JWT (cualquier rol)
- **Query params**: `?periodo=:id&page=1&limit=10&search=nombre_o_nrc`
- **Response 200**: Lista paginada de materias con filtro por periodo y búsqueda

#### `GET /materias/:id`
- **Auth**: JWT (cualquier rol)
- **Response 200**: Detalle completo de la materia

#### `POST /periodos/:id/importar`
- **Auth**: JWT + rol `admin`
- **Content-Type**: `multipart/form-data`
- **Body**: `file` (archivo PDF)
- **Lógica de importación**:
  1. Recibir PDF de programación académica oficial
  2. Parsear con `pdfplumber`:
     - Extraer NRC
     - Extraer nombre de materia
     - Extraer sección
     - Extraer clave de materia
     - Extraer nombre de docente asignado
     - Extraer horario (días y horas)
  3. Normalizar datos (quitar espacios extras, corregir encoding)
  4. Persistir cada materia en la BD del periodo indicado
  5. Si el NRC ya existe en ese periodo → actualizar, no duplicar
- **Response 200**:
  ```json
  {
    "success": true,
    "data": {
      "importadas": 45,
      "actualizadas": 3,
      "fallidas": 2,
      "errores": [
        { "fila": 23, "motivo": "NRC vacío" }
      ]
    }
  }
  ```
- **Response 400**: PDF corrupto o formato no reconocido

#### `PUT /materias/:id`
- **Auth**: JWT + rol `admin`
- **Body**: Campos a actualizar manualmente
- **Response 200**: Materia actualizada

#### `DELETE /materias/:id`
- **Auth**: JWT + rol `admin`
- **Validación**: Solo si no tiene alumnos inscritos (verificar con gRPC a MS-3)
- **Response 200**: Materia eliminada
- **Response 400**: "No se puede eliminar una materia con alumnos inscritos"

---

## Servidor gRPC (Puerto 50052)

### Archivo proto: `/proto/periodos.proto`
```protobuf
syntax = "proto3";
package periodos;

service PeriodosService {
  rpc GetMateriaById(GetMateriaByIdRequest) returns (MateriaInfo);
  rpc GetMateriasByDocente(GetMateriasByDocenteRequest) returns (MateriasListResponse);
  rpc GetPeriodoActivo(Empty) returns (PeriodoInfo);
}

message Empty {}

message GetMateriaByIdRequest {
  int32 materia_id = 1;
}

message MateriaInfo {
  int32 id = 1;
  string nrc = 2;
  string nombre = 3;
  string seccion = 4;
  string clave = 5;
  string docente_nombre = 6;
  int32 docente_id = 7;
  string horario = 8;
  int32 periodo_id = 9;
  string periodo_nombre = 10;
}

message GetMateriasByDocenteRequest {
  int32 docente_id = 1;
}

message MateriasListResponse {
  repeated MateriaInfo materias = 1;
}

message PeriodoInfo {
  int32 id = 1;
  string nombre = 2;
  string fecha_inicio = 3;
  string fecha_fin = 4;
  string plan_estudios = 5;
  bool activo = 6;
}
```

---

## Clientes gRPC (este MS llama a)

| MS destino | Método | Cuándo |
|-----------|--------|--------|
| MS-1 Auth | `ValidateToken` | En CADA request protegido para validar el JWT |
| MS-1 Auth | `CheckRole` | Para verificar que el usuario es admin en endpoints de escritura |
| MS-3 Alumnos | `GetAlumnosByMateria` | Al intentar eliminar una materia (verificar que no tenga alumnos) |

---

## Variables de Entorno (`.env.example`)

```env
SECRET_KEY=django-insecure-cambiar
DEBUG=True
ALLOWED_HOSTS=*

DB_HOST=db-periodos
DB_PORT=3306
DB_NAME=agm_periodos_db
DB_USER=root
DB_PASSWORD=root_password

REST_PORT=8002
GRPC_PORT=50052

# gRPC hacia otros MS
MS_AUTH_GRPC_HOST=ms-auth
MS_AUTH_GRPC_PORT=50051
MS_ALUMNOS_GRPC_HOST=ms-alumnos
MS_ALUMNOS_GRPC_PORT=50053
```

---

## Reglas de Negocio Críticas

1. **Solo puede existir UN periodo activo a la vez** — esto es la regla más importante de este MS
2. Al activar un periodo, se desactivan automáticamente todos los demás (transacción atómica)
3. Las fechas del periodo deben ser coherentes: `fecha_inicio < fecha_fin`
4. No se puede eliminar un periodo que tenga materias asociadas
5. No se puede eliminar una materia que tenga alumnos inscritos
6. El NRC es único dentro de un periodo (pero puede repetirse entre periodos distintos)
7. La importación de PDF debe ser tolerante a errores: si una fila falla, las demás deben procesarse
8. El campo `docente_id` se llena opcionalmente si se puede mapear al MS-3

---

## Notas sobre Parsing de PDF

El PDF de programación académica de la BUAP típicamente tiene formato tabular con columnas:
- NRC | Clave | Materia | Sección | Docente | Horario

Para el parsing con `pdfplumber`:
```python
import pdfplumber

def parsear_pdf_materias(archivo_pdf):
    materias = []
    with pdfplumber.open(archivo_pdf) as pdf:
        for page in pdf.pages:
            tabla = page.extract_table()
            if tabla:
                for fila in tabla[1:]:  # Saltar encabezado
                    if len(fila) >= 6:
                        materias.append({
                            'nrc': fila[0].strip() if fila[0] else '',
                            'clave': fila[1].strip() if fila[1] else '',
                            'nombre': fila[2].strip() if fila[2] else '',
                            'seccion': fila[3].strip() if fila[3] else '',
                            'docente_nombre': fila[4].strip() if fila[4] else '',
                            'horario': fila[5].strip() if fila[5] else '',
                        })
    return materias
```

> **NOTA**: El parsing exacto depende del formato real del PDF de la BUAP. Esto es un esqueleto que debe ajustarse al PDF real.
