"""
Script para exportar la base de datos de trabajadores BUAP a CSV
y generar un SQL de seed para MySQL (MS-3 Docentes & Alumnos).

Uso:
    python export_trabajadores.py

Genera:
    - test-data/trabajadores_buap.csv          (CSV universal)
    - test-data/seed_docentes_mysql.sql         (INSERT INTO para MySQL)
"""

import sqlite3
import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "buap_trabajadores.db")
CSV_PATH = os.path.join(BASE_DIR, "trabajadores_buap.csv")
SQL_PATH = os.path.join(BASE_DIR, "seed_docentes_mysql.sql")


def title_case(s):
    """Convierte 'PEREZ BONILLA' a 'Pérez Bonilla' de forma simple."""
    if not s:
        return ""
    return " ".join(word.capitalize() for word in s.strip().split())


def export_csv(cur):
    """Exporta todos los trabajadores a CSV."""
    cur.execute("SELECT matricula, paterno, materno, nombre, email FROM trabajadores ORDER BY matricula")
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
    """Genera un archivo SQL con INSERTs para MySQL (tabla docente de MS-3)."""
    cur.execute("""
        SELECT matricula, paterno, materno, nombre, email 
        FROM trabajadores 
        WHERE email != '' AND email IS NOT NULL
        ORDER BY matricula
    """)
    rows = cur.fetchall()

    with open(SQL_PATH, "w", encoding="utf-8") as f:
        f.write("-- =============================================\n")
        f.write("-- Seed de docentes BUAP para MS-3 (agm_alumnos_db)\n")
        f.write("-- Generado desde buap_trabajadores.db\n")
        f.write(f"-- Total: {len(rows)} docentes con email\n")
        f.write("-- Encoding: UTF-8 (compatible con utf8mb4)\n")
        f.write("-- =============================================\n\n")
        f.write("-- Asegurar encoding correcto para acentos y ñ\n")
        f.write("SET NAMES utf8mb4;\n")
        f.write("SET CHARACTER SET utf8mb4;\n\n")
        f.write("USE agm_alumnos_db;\n\n")
        f.write("-- Limpiar tabla antes de insertar (opcional)\n")
        f.write("-- TRUNCATE TABLE core_docente;\n\n")
        f.write("INSERT INTO core_docente (usuario_id, nombre, email_institucional, cubiculo, fecha_creacion, fecha_actualizacion) VALUES\n")

        lines = []
        for i, row in enumerate(rows):
            matricula, paterno, materno, nombre, email = row
            nombre_completo = f"{title_case(nombre)} {title_case(paterno)} {title_case(materno)}".strip()
            # Escapar comillas simples en nombres
            nombre_completo = nombre_completo.replace("'", "\\'")
            email_clean = (email or "").replace("'", "\\'")
            # usuario_id será la matrícula temporalmente (se actualiza cuando se cree el user en MS-1)
            lines.append(f"  ({matricula}, '{nombre_completo}', '{email_clean}', NULL, NOW(), NOW())")

        f.write(",\n".join(lines))
        f.write(";\n")

    print(f"SQL seed exportado: {SQL_PATH} ({len(rows)} docentes con email)")


def print_stats(cur):
    """Muestra estadísticas útiles."""
    cur.execute("SELECT COUNT(*) FROM trabajadores")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM trabajadores WHERE email != '' AND email IS NOT NULL")
    con_email = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM trabajadores WHERE email = '' OR email IS NULL")
    sin_email = cur.fetchone()[0]

    print(f"\n=== ESTADÍSTICAS ===")
    print(f"  Total trabajadores:  {total:,}")
    print(f"  Con email:           {con_email:,}")
    print(f"  Sin email:           {sin_email:,}")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    export_csv(cur)
    export_mysql_seed(cur)
    print_stats(cur)

    conn.close()
    print("\n✅ Listo. Archivos generados en test-data/")
