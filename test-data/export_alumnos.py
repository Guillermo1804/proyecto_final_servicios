"""
Script para exportar la base de datos de alumnos BUAP a CSV
y generar un SQL de seed para MySQL (MS-3 Docentes & Alumnos).

Uso:
    python export_alumnos.py

Genera:
    - test-data/alumnos_buap.csv              (CSV universal)
    - test-data/seed_alumnos_mysql.sql         (INSERT INTO para MySQL)
"""

import sqlite3
import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "buap_alumnos.db")
CSV_PATH = os.path.join(BASE_DIR, "alumnos_buap.csv")
SQL_PATH = os.path.join(BASE_DIR, "seed_alumnos_mysql.sql")


def title_case(s):
    if not s:
        return ""
    return " ".join(word.capitalize() for word in s.strip().split())


def export_csv(cur):
    cur.execute("SELECT matricula, paterno, materno, nombre, email FROM alumnos ORDER BY matricula")
    rows = cur.fetchall()

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["matricula", "apellido_paterno", "apellido_materno", "nombre", "nombre_completo", "email"])
        for row in rows:
            matricula, paterno, materno, nombre, email = row
            nombre_completo = f"{title_case(nombre)} {title_case(paterno)} {title_case(materno)}".strip()
            writer.writerow([
                matricula,
                title_case(paterno),
                title_case(materno),
                title_case(nombre),
                nombre_completo,
                email or ""
            ])

    print(f"CSV exportado: {CSV_PATH} ({len(rows)} registros)")
    return rows


def export_mysql_seed(cur):
    cur.execute("""
        SELECT matricula, paterno, materno, nombre, email
        FROM alumnos
        WHERE email != '' AND email IS NOT NULL
        ORDER BY matricula
    """)
    rows = cur.fetchall()

    with open(SQL_PATH, "w", encoding="utf-8") as f:
        f.write("-- =============================================\n")
        f.write("-- Seed de alumnos BUAP para MS-3 (agm_alumnos_db)\n")
        f.write("-- Generado desde buap_alumnos.db\n")
        f.write(f"-- Total: {len(rows)} alumnos con email\n")
        f.write("-- Encoding: UTF-8 (compatible con utf8mb4)\n")
        f.write("-- =============================================\n\n")
        f.write("-- Asegurar encoding correcto para acentos y ñ\n")
        f.write("SET NAMES utf8mb4;\n")
        f.write("SET CHARACTER SET utf8mb4;\n\n")
        f.write("USE agm_alumnos_db;\n\n")
        f.write("-- Limpiar tabla antes de insertar (opcional)\n")
        f.write("-- TRUNCATE TABLE core_alumno;\n\n")

        # Insertar en bloques de 1000 para no exceder limites de MySQL
        batch_size = 1000
        for batch_start in range(0, len(rows), batch_size):
            batch = rows[batch_start:batch_start + batch_size]
            f.write(f"-- Bloque {batch_start // batch_size + 1}\n")
            f.write("INSERT INTO core_alumno (usuario_id, matricula, nombre, email, tipo_formacion, fecha_creacion) VALUES\n")

            lines = []
            for row in batch:
                matricula, paterno, materno, nombre, email = row
                nombre_completo = f"{title_case(nombre)} {title_case(paterno)} {title_case(materno)}".strip()
                nombre_completo = nombre_completo.replace("'", "\\'")
                email_clean = (email or "").replace("'", "\\'")
                lines.append(f"  ({matricula}, '{matricula}', '{nombre_completo}', '{email_clean}', 'Licenciatura', NOW())")

            f.write(",\n".join(lines))
            f.write(";\n\n")

    print(f"SQL seed exportado: {SQL_PATH} ({len(rows)} alumnos con email)")


def print_stats(cur):
    cur.execute("SELECT COUNT(*) FROM alumnos")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM alumnos WHERE email != '' AND email IS NOT NULL")
    con_email = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM alumnos WHERE email = '' OR email IS NULL")
    sin_email = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM alumnos WHERE email LIKE '%@alumno.buap.mx'")
    email_buap = cur.fetchone()[0]

    print(f"\n=== ESTADISTICAS ===")
    print(f"  Total alumnos:       {total:,}")
    print(f"  Con email:           {con_email:,}")
    print(f"  Sin email:           {sin_email:,}")
    print(f"  Email @alumno.buap:  {email_buap:,}")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    export_csv(cur)
    export_mysql_seed(cur)
    print_stats(cur)

    conn.close()
    print("\nListo. Archivos generados en test-data/")
