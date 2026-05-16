# AGM Postman Collection

Este directorio contiene la colección de Postman y el entorno para probar las APIs de los microservicios del proyecto AGM.

## Archivos

- `AGM_API_Collection.json`: Colección con todos los endpoints de `ms-periodos` y `ms-alumnos`.
- `AGM_Environment.json`: Variables de entorno para facilitar el cambio entre local y otros ambientes.

## Instrucciones de Importación

1. Abrir Postman.
2. Hacer clic en **Import**.
3. Seleccionar ambos archivos (`AGM_API_Collection.json` y `AGM_Environment.json`).
4. En la esquina superior derecha, seleccionar el environment **AGM Local Environment**.

## Variables de Entorno

- `base_url_periodos`: URL base para el microservicio de periodos (default: `http://localhost:8002`).
- `base_url_alumnos`: URL base para el microservicio de alumnos (default: `http://localhost:8003`).

## Endpoints Incluidos

### MS Periodos (Port 8002)
- CRUD de Periodos
- Activar Periodo
- Consultar Periodo Activo
- CRUD de Materias
- Importar Materias desde Excel

### MS Alumnos (Port 8003)
- CRUD de Docentes
- Importación de Alumnos (Preview y Confirmar)
- Listado de Alumnos por Materia
- Baja de Materia
