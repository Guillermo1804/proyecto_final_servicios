# Datos de Prueba

Archivos de datos reales y de prueba para el sistema AGM.

---

## Base de Datos de Trabajadores BUAP (Docentes)

| Archivo | Formato | Registros | Descripción |
|---------|---------|-----------|-------------|
| `buap_trabajadores.db` | SQLite | 43,025 | BD original con todos los trabajadores de la BUAP |
| `trabajadores_buap.csv` | CSV | 43,025 | Exportación con nombres formateados (Title Case) |
| `seed_docentes_mysql.sql` | SQL | 13,157 | INSERTs listos para MySQL (solo trabajadores con email) |
| `export_trabajadores.py` | Python | — | Script para regenerar CSV y SQL desde la BD SQLite |

## Base de Datos de Alumnos BUAP

| Archivo | Formato | Registros | Descripción |
|---------|---------|-----------|-------------|
| `buap_alumnos.db` | SQLite | 318,374 | BD original con todos los alumnos de la BUAP |
| `alumnos_buap.csv` | CSV | 318,374 | Exportación con nombres formateados (Title Case) |
| `seed_alumnos_mysql.sql` | SQL | 316,807 | INSERTs listos para MySQL en bloques de 1000 (alumnos con email) |
| `export_alumnos.py` | Python | — | Script para regenerar CSV y SQL desde la BD SQLite |

### Uso rápido
```bash
# Cargar datos en MySQL después de correr migraciones de MS-3
mysql -u root -p agm_alumnos_db < test-data/seed_docentes_mysql.sql
mysql -u root -p agm_alumnos_db < test-data/seed_alumnos_mysql.sql
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

- `lista_alumnos_ejemplo.xlsx` — Excel de ejemplo con lista de alumnos (para probar import en MS-3)

> **Nota sobre datos sensibles**: Estas BDs contienen datos de directorio público
> de una institución pública. No contienen datos privados sensibles.