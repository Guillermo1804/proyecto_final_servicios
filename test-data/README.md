# Datos de Prueba

Archivos de datos reales y de prueba para el sistema AGM.

---

## Base de Datos de Trabajadores BUAP

| Archivo | Formato | Registros | Descripción |
|---------|---------|-----------|-------------|
| `buap_trabajadores.db` | SQLite | 43,025 | BD original con todos los trabajadores de la BUAP |
| `trabajadores_buap.csv` | CSV | 43,025 | Exportación con nombres formateados (Title Case) |
| `seed_docentes_mysql.sql` | SQL | 13,157 | INSERTs listos para MySQL (solo trabajadores con email) |
| `export_trabajadores.py` | Python | — | Script para regenerar CSV y SQL desde la BD SQLite |

### Uso rápido
```bash
# Cargar docentes en MySQL después de correr migraciones de MS-3
mysql -u root -p agm_alumnos_db < test-data/seed_docentes_mysql.sql
```

---

## PDFs de Programación Académica

PDFs oficiales de la BUAP para probar la importación de materias (MS-2):

| Archivo | Carrera |
|---------|---------|
| `PA_PRIMAVERA_2025_SEMESTRAL_ITI.pdf` | ITI - Primavera 2025 |
| `PA_PRIMAVERA_2024_SEMESTRAL_ITI.pdf` | ITI - Primavera 2024 |
| `PA_ITI_CU_21_NOV_2025.pdf` | ITI - CU Nov 2025 |
| `*CCO*.pdf` | Ciencias de la Computación |
| `*ICC*.pdf` | Ingeniería en Ciencias de la Computación |
| `*ICD*.pdf` | Ingeniería en Ciencia de Datos |
| `*ICS*.pdf` | Ingeniería en Ciberseguridad |
| `*ITI*.pdf` | Ingeniería en Tecnologías de la Información |

---

## Archivos pendientes de crear

- `lista_alumnos_ejemplo.xlsx` — Excel de ejemplo con lista de alumnos (para importar en MS-3)

> **Nota sobre datos sensibles**: Esta BD contiene datos de trabajadores públicos
> de una institución pública. Los nombres y correos institucionales son información
> de directorio público. No contiene datos privados sensibles.