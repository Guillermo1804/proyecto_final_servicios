from __future__ import annotations

import pdfplumber
import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
UBICACION_RE = re.compile(r"CCO\d+-\d+", re.IGNORECASE)
SKIP_LINE_MARKERS = (
    "autoservicios",
    "correo buap",
    "facultad de ciencias",
    "inicio >",
    "personal docente",
    "correo electr",
    "ubicación:",
    "ubicacion:",
    "extensión:",
    "extension:",
    "oferta acad",
    "secretaría",
    "investigación",
    "vinculación",
    "redes sociales",
)


def _is_header_row(cells: list[str]) -> bool:
    joined = " ".join(cells).lower()
    return (
        "correo" in joined
        or "ubicacion" in joined
        or "ubicación" in joined
        or "extension" in joined
        or "extensión" in joined
        or ("nombre" in joined and "@" not in joined)
    )


def _find_email_column(cells: list[str]) -> int | None:
    for idx, cell in enumerate(cells):
        if EMAIL_RE.search(cell.replace("\n", " ")):
            return idx
    return None


def _split_nombre_buap(full_name: str) -> tuple[str, str]:
    """Ej: 'Acosta Ruiz Samantha' -> nombre='Samantha', apellido='Acosta Ruiz'."""
    parts = [p for p in full_name.replace("\n", " ").split() if p]
    if len(parts) >= 2:
        return parts[-1], " ".join(parts[:-1])
    if len(parts) == 1:
        return parts[0], ""
    return "", ""


def _build_docente_row(
    full_name: str,
    email: str,
    tail: str = "",
) -> dict | None:
    nombre, apellido = _split_nombre_buap(full_name)
    if not nombre and not apellido:
        return None

    ubicacion = ""
    extension = ""
    ubi_m = UBICACION_RE.search(tail)
    if ubi_m:
        ubicacion = ubi_m.group(0)
        tail = tail[ubi_m.end() :].strip()
    ext_m = re.search(r"\b\d{4}\b", tail)
    if ext_m:
        extension = ext_m.group(0)

    departamento = ubicacion or "Sin ubicacion"
    if extension:
        departamento = f"{departamento} (ext. {extension})"

    return {
        "nombre": nombre or apellido,
        "apellido": apellido if nombre else "",
        "email": email.lower(),
        "departamento": departamento,
    }


def _parse_row(cells: list[str]) -> dict | None:
    clean_row = [str(cell or "").strip() for cell in cells]
    if not any(clean_row):
        return None
    if _is_header_row(clean_row):
        return None

    email_idx = _find_email_column(clean_row)
    if email_idx is None:
        return None

    email_m = EMAIL_RE.search(clean_row[email_idx].replace("\n", " "))
    if not email_m:
        return None

    email = email_m.group(0)
    line_joined = " ".join(clean_row)

    if email_idx == 1:
        full_name = clean_row[0].replace("\n", " ").strip()
        tail = " ".join(clean_row[2:]).strip()
        return _build_docente_row(full_name, email, tail)

    if email_idx == 2 and len(clean_row) >= 4:
        return {
            "nombre": clean_row[0],
            "apellido": clean_row[1],
            "email": email.lower(),
            "departamento": clean_row[3] if len(clean_row) > 3 else "Sin ubicacion",
        }

    before = " ".join(c.replace("\n", " ").strip() for c in clean_row[:email_idx] if c.strip())
    tail = " ".join(c.strip() for c in clean_row[email_idx + 1 :] if c.strip())
    return _build_docente_row(before, email, tail)


def _should_skip_text_line(line: str) -> bool:
    low = line.lower().strip()
    if len(low) < 12:
        return True
    if "@" not in line:
        return True
    return any(marker in low for marker in SKIP_LINE_MARKERS)


def _parse_text_line(line: str) -> dict | None:
    """PDFs impresos desde la web BUAP: datos en texto, no en celdas de tabla."""
    if _should_skip_text_line(line):
        return None

    email_m = EMAIL_RE.search(line)
    if not email_m:
        return None

    email = email_m.group(0)
    if "buap" not in email.lower():
        return None

    before = line[: email_m.start()].strip()
    after = line[email_m.end() :].strip()
    return _build_docente_row(before, email, after)


def _parse_from_tables(pdf) -> tuple[list[dict], list[str], int]:
    rows: list[dict] = []
    errors: list[str] = []
    pages_with_tables = 0
    seen: set[str] = set()

    for page_num, page in enumerate(pdf.pages, start=1):
        tables = page.extract_tables()
        if not tables:
            continue
        pages_with_tables += 1
        for table in tables:
            for r_idx, row in enumerate(table):
                try:
                    parsed = _parse_row(row)
                except Exception as exc:
                    errors.append(f"Pag {page_num}, fila {r_idx}: {exc}")
                    continue
                if not parsed or parsed["email"] in seen:
                    continue
                seen.add(parsed["email"])
                rows.append(parsed)

    return rows, errors, pages_with_tables


def _parse_from_text(pdf) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    errors: list[str] = []
    seen: set[str] = set()

    for page_num, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                parsed = _parse_text_line(line)
            except Exception as exc:
                errors.append(f"Pag {page_num}, linea texto: {exc}")
                continue
            if not parsed or parsed["email"] in seen:
                continue
            seen.add(parsed["email"])
            rows.append(parsed)

    return rows, errors


def parse_pdf_docentes(file_path):
    """
    Extrae docentes de PDF tipo directorio BUAP (pdfplumber, sin IA).

    Muchos PDFs guardados desde Chrome solo exponen el encabezado como tabla;
    las filas van en texto plano -> fallback por linea con correo @correo.buap.mx.
    """
    rows: list[dict] = []
    errors: list[str] = []

    try:
        with pdfplumber.open(file_path) as pdf:
            if not pdf.pages:
                errors.append("El PDF no tiene paginas legibles.")
                return rows, errors

            rows, errors, pages_with_tables = _parse_from_tables(pdf)

            if len(rows) < 2:
                text_rows, text_errors = _parse_from_text(pdf)
                errors.extend(text_errors)
                if text_rows:
                    errors.append(
                        f"Parser texto: {len(text_rows)} filas "
                        f"(tablas solo dieron {len(rows)})."
                    )
                    rows = text_rows

            if not rows and pages_with_tables == 0:
                errors.append(
                    "No hubo tablas ni lineas con correo en el PDF. "
                    "Exporte de nuevo desde el navegador (Ctrl+P)."
                )
            elif not rows:
                errors.append(
                    "No se encontraron lineas con nombre y correo @correo.buap.mx."
                )

    except Exception as e:
        errors.append(f"Error critico al leer PDF: {str(e)}")

    return rows, errors
