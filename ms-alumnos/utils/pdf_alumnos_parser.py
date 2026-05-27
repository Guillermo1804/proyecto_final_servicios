"""Parser PDF lista de clase BUAP (Servicios Web → Ctrl+P / Guardar como PDF)."""

from __future__ import annotations

import re

import pdfplumber

# Matricula BUAP: 202224429, 202213377, etc.
MATRICULA_RE = re.compile(r"\b(20\d{7,9})\b")
NRC_RE = re.compile(r"NRC:\s*(\d+)", re.IGNORECASE)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
MAILTO_RE = re.compile(r"mailto:([^?\s#]+)", re.IGNORECASE)
# Fila tipica: "1 AGUILAR SALDIVAR, ANGEL G. 202224429 **Inscrito..."
CLASS_ROW_RE = re.compile(
    r"^\s*(\d{1,3})\s+(.+?)\s+(20\d{7,9})(?:\s+|\*|$)",
)
DOCENTE_HEADER_RE = re.compile(
    r"lista de clase\s+\d+\s+(.+?)\s*-\s*(.+?)\s*$",
    re.IGNORECASE,
)
PERIODO_RE = re.compile(
    r"^(Primavera|Verano|Otoño|Otono)\s+(\d{4})\s*$",
    re.IGNORECASE,
)
SKIP_MARKERS = (
    "resumen de lista",
    "información de curso",
    "informacion de curso",
    "conteo de ingreso",
    "número nombre",
    "numero nombre",
    "número de registro",
    "numero de registro",
    "nombre de alumno",
    "máximo real",
    "maximo real",
    "un asterisco",
    "si aparece la palabra",
    "lista cruzada",
    "ingreso:",
    "duración:",
    "duracion:",
    "status: activo",
    "detalle de",
    "calificaciones",
    "status de",
    "de inscripci",
)


def _split_nombre_buap(full_name: str) -> tuple[str, str]:
    """
    Formato BUAP en lista de clase: 'APELLIDO(S), NOMBRE'.
    Ej: 'AGUILAR SALDIVAR, ANGEL G.' -> apellido, nombre.
    Caso raro: 'HERNANDEZ PALESTINA,' (sin nombre) -> todo en nombre.
    """
    cleaned = re.sub(r"\s+", " ", full_name.replace("\n", " ")).strip().rstrip(",")
    if not cleaned:
        return "", ""
    if "," in full_name.replace("\n", " "):
        apellido, nombre = full_name.replace("\n", " ").split(",", 1)
        apellido = apellido.strip().rstrip(",")
        nombre = nombre.strip()
        if not nombre:
            return "", apellido or cleaned
        return apellido, nombre
    parts = [p for p in cleaned.split() if p]
    if len(parts) >= 3:
        return " ".join(parts[:-1]), parts[-1]
    if len(parts) == 2:
        # Sin coma: p. ej. "HERNANDEZ PALESTINA" (nombre incompleto en PDF)
        return "", cleaned
    return "", parts[0]


def _build_alumno_row(matricula: str, name_part: str) -> dict | None:
    name_part = name_part.strip().rstrip(",")
    if not name_part:
        return None
    apellido, nombre = _split_nombre_buap(name_part)
    if not nombre and not apellido:
        return None
    return {
        "matricula": matricula,
        "nombre": nombre or apellido,
        "apellido": apellido if nombre else "",
        "email": "",
        "carrera": "ICC",
        "semestre": 1,
    }


def _parse_class_line(line: str) -> dict | None:
    stripped = line.strip()
    row_m = CLASS_ROW_RE.match(stripped)
    if row_m:
        return _build_alumno_row(row_m.group(3), row_m.group(2))

    mat_m = MATRICULA_RE.search(stripped)
    if not mat_m:
        return None
    before = stripped[: mat_m.start()].strip()
    before = re.sub(r"^\d{1,3}\s+", "", before)
    return _build_alumno_row(mat_m.group(1), before)


def _parse_table_row(cells: list) -> dict | None:
    """Tablas exportadas con columnas Numero | Nombre | ID | ..."""
    clean = [str(c or "").replace("\n", " ").strip() for c in cells]
    if not any(clean):
        return None
    joined = " ".join(clean).lower()
    if "nombre de alumno" in joined or "número" in joined or "numero" in joined:
        return None

    matricula = ""
    name_part = ""
    for cell in clean:
        if MATRICULA_RE.fullmatch(cell):
            matricula = cell
            break
    if not matricula:
        for cell in clean:
            m = MATRICULA_RE.search(cell)
            if m:
                matricula = m.group(1)
                break

    if not matricula:
        return None

    if len(clean) >= 3 and MATRICULA_RE.fullmatch(clean[2]):
        name_part = clean[1]
    elif len(clean) >= 2:
        name_part = clean[1] if MATRICULA_RE.fullmatch(clean[-1]) else clean[0]

    return _build_alumno_row(matricula, name_part)


def _should_skip_line(line: str) -> bool:
    low = line.lower().strip()
    if len(low) < 10:
        return True
    if not MATRICULA_RE.search(line):
        return True
    if not re.match(r"^\s*\d{1,3}\s+", line):
        return True
    return any(marker in low for marker in SKIP_MARKERS)


def _extract_meta(text: str) -> dict:
    meta: dict = {
        "nrc": "",
        "nombre_materia": "",
        "docente": "",
        "periodo": "",
        "clave": "",
    }
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    nrc_m = NRC_RE.search(text)
    if nrc_m:
        meta["nrc"] = nrc_m.group(1)

    for line in lines:
        doc_m = DOCENTE_HEADER_RE.search(line)
        if doc_m:
            meta["docente"] = f"{doc_m.group(1).strip()} {doc_m.group(2).strip()}".strip()
        per_m = PERIODO_RE.match(line)
        if per_m:
            meta["periodo"] = f"{per_m.group(1)} {per_m.group(2)}"

    for i, line in enumerate(lines):
        low = line.lower()
        if "informaci" in low and "curso" in low:
            for j in range(i + 1, min(i + 5, len(lines))):
                cand = lines[j]
                if not cand or cand.lower().startswith("nrc:"):
                    continue
                if "duraci" in cand.lower() or "status:" in cand.lower():
                    continue
                meta["nombre_materia"] = cand
                meta["clave"] = cand
                break
            break

    return meta


def _parse_from_tables(pdf) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    errors: list[str] = []
    seen: set[str] = set()

    for page_num, page in enumerate(pdf.pages, start=1):
        for table in page.extract_tables() or []:
            for r_idx, raw_row in enumerate(table):
                try:
                    parsed = _parse_table_row(raw_row)
                except Exception as exc:
                    errors.append(f"Pag {page_num}, tabla fila {r_idx}: {exc}")
                    continue
                if not parsed or parsed["matricula"] in seen:
                    continue
                seen.add(parsed["matricula"])
                rows.append(parsed)

    return rows, errors


def _parse_from_text(pdf) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    errors: list[str] = []
    seen: set[str] = set()

    for page_num, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if _should_skip_line(line):
                continue
            try:
                parsed = _parse_class_line(line)
            except Exception as exc:
                errors.append(f"Pag {page_num}: {exc}")
                continue
            if not parsed or parsed["matricula"] in seen:
                continue
            seen.add(parsed["matricula"])
            rows.append(parsed)

    return rows, errors


def _extract_emails_from_hyperlinks(pdf) -> list[str]:
    """
    En listas BUAP (Ctrl+P) el correo no va en el texto visible: va en enlaces mailto:.
    pdfplumber los expone en page.hyperlinks / page.annots.
    """
    emails: list[str] = []
    seen: set[str] = set()

    for page in pdf.pages:
        page_links: list[tuple[str, float]] = []
        for link in page.hyperlinks or []:
            uri = str(link.get("uri") or "")
            mail_m = MAILTO_RE.search(uri)
            if not mail_m:
                continue
            email = mail_m.group(1).strip().lower()
            if not email or "@" not in email:
                continue
            page_links.append((email, float(link.get("top") or 0)))

        page_links.sort(key=lambda item: item[1])
        for email, _top in page_links:
            if email in seen:
                continue
            seen.add(email)
            emails.append(email)

    return emails


def _attach_emails_to_rows(
    rows: list[dict],
    emails: list[str],
    errors: list[str],
) -> None:
    """Asocia correos mailto: a filas por orden vertical (misma secuencia que Servicios Web)."""
    if not rows:
        return

    text_emails = [
        (idx, EMAIL_RE.search(" ".join(
            (row.get("nombre", ""), row.get("apellido", ""), row.get("matricula", ""))
        )))
        for idx, row in enumerate(rows)
    ]
    for idx, match in text_emails:
        if match:
            rows[idx]["email"] = match.group(0).lower()

    pending = [i for i, row in enumerate(rows) if not row.get("email")]
    if not emails:
        if pending:
            errors.append(
                "No se encontraron enlaces mailto: con correo en el PDF. "
                "Use la lista exportada desde Servicios Web (no escanear)."
            )
        return

    if len(emails) != len(pending) and len(emails) != len(rows):
        errors.append(
            f"Correos mailto ({len(emails)}) no coinciden con filas ({len(rows)}). "
            "Se asignaran en orden hasta donde alcance."
        )

    email_iter = iter(emails)
    for idx in pending:
        try:
            rows[idx]["email"] = next(email_iter)
        except StopIteration:
            break

    with_email = sum(1 for row in rows if row.get("email"))
    if with_email:
        errors.append(f"Correos asignados: {with_email} de {len(rows)} (via mailto:/texto).")


def parse_pdf_alumnos(file_path: str) -> tuple[list[dict], list[str], dict]:
    """
    Extrae alumnos del PDF oficial de lista de clase (Servicios Web BUAP).

    Retorna (filas, errores_parseo, meta) con nrc, nombre_materia, docente, periodo.
    """
    rows: list[dict] = []
    errors: list[str] = []
    meta: dict = {
        "nrc": "",
        "nombre_materia": "",
        "docente": "",
        "periodo": "",
        "clave": "",
    }

    try:
        with pdfplumber.open(file_path) as pdf:
            if not pdf.pages:
                errors.append("El PDF no tiene paginas legibles.")
                return rows, errors, meta

            full_text = "\n".join((page.extract_text() or "") for page in pdf.pages)
            meta = _extract_meta(full_text)

            table_rows, table_errors = _parse_from_tables(pdf)
            errors.extend(table_errors)

            if len(table_rows) >= 2:
                rows = table_rows
                errors.append(f"Parser tablas: {len(table_rows)} filas.")
            else:
                text_rows, text_errors = _parse_from_text(pdf)
                errors.extend(text_errors)
                if text_rows:
                    if table_rows:
                        errors.append(
                            f"Parser texto: {len(text_rows)} filas "
                            f"(tablas solo dieron {len(table_rows)})."
                        )
                    rows = text_rows

            if not rows:
                errors.append(
                    "No se encontraron alumnos con matricula 20XXXXXXXX. "
                    "Exporte la lista desde Servicios Web (Imprimir / Guardar PDF)."
                )
            else:
                mailto_emails = _extract_emails_from_hyperlinks(pdf)
                _attach_emails_to_rows(rows, mailto_emails, errors)

    except Exception as exc:
        errors.append(f"Error critico al leer PDF: {exc}")

    return rows, errors, meta
