"""Generación de reportes PDF desde DTOs (reportlab)."""

import os
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.reportes.dto.report_dto import AsistenciasReportDTO, CalificacionesReportDTO

_FONT_REGISTERED = False


def _register_utf8_font() -> str:
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return 'AGMUTF8' if 'AGMUTF8' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'

    candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        'C:/Windows/Fonts/arial.ttf',
    ]
    for path in candidates:
        if os.path.isfile(path):
            pdfmetrics.registerFont(TTFont('AGMUTF8', path))
            _FONT_REGISTERED = True
            return 'AGMUTF8'
    _FONT_REGISTERED = True
    return 'Helvetica'


def _paragraph(text: str, style) -> Paragraph:
    return Paragraph(str(text).replace('\n', '<br/>'), style)


def _actividad_columnas(dto: CalificacionesReportDTO) -> list[tuple[int, str]]:
    columnas: list[tuple[int, str]] = []
    for cat in dto.categorias:
        for act in cat.actividades:
            columnas.append((act.actividad_id, f'{act.nombre} ({cat.nombre})'))
    return columnas


def build_calificaciones_pdf(dto: CalificacionesReportDTO) -> BytesIO:
    font = _register_utf8_font()
    styles = getSampleStyleSheet()
    body = styles['Normal']
    body.fontName = font
    title_style = styles['Heading2']
    title_style.fontName = font

    buffer = BytesIO()
    m = dto.materia
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    story = [
        _paragraph('BUAP — Facultad de Ciencias de la Computación', title_style),
        _paragraph(f'Materia: {m.nombre}', body),
        _paragraph(f'NRC: {m.nrc} | Sección: {m.seccion} | Clave: {m.clave}', body),
        _paragraph(
            f'Periodo: {m.periodo_nombre} | Docente: {m.docente_nombre} | Horario: {m.horario}',
            body,
        ),
        Spacer(1, 12),
    ]

    columnas_act = _actividad_columnas(dto)
    header = ['Matrícula', 'Nombre'] + [label for _, label in columnas_act] + [
        'Promedio Real',
        'Prom. Red.',
    ]
    data = [header]
    for alumno in dto.alumnos:
        notas = {c.actividad_id: c.calificacion for c in alumno.calificaciones}
        data.append(
            [
                alumno.matricula,
                alumno.nombre,
                *[str(notas.get(act_id, '')) for act_id, _ in columnas_act],
                f'{alumno.promedio_real:.2f}',
                str(alumno.promedio_redondeado),
            ]
        )

    col_count = len(header)
    col_width = doc.width / max(col_count, 1)
    table = Table(data, colWidths=[col_width] * col_count, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, -1), font),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer


def build_asistencias_pdf(dto: AsistenciasReportDTO) -> BytesIO:
    font = _register_utf8_font()
    styles = getSampleStyleSheet()
    body = styles['Normal']
    body.fontName = font
    title_style = styles['Heading2']
    title_style.fontName = font

    buffer = BytesIO()
    m = dto.materia
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch)
    story = [
        _paragraph('BUAP — Facultad de Ciencias de la Computación', title_style),
        _paragraph(f'Materia: {m.nombre}', body),
        _paragraph(f'NRC: {m.nrc} | Sección: {m.seccion} | Clave: {m.clave}', body),
        _paragraph(
            f'Periodo: {m.periodo_nombre} | Docente: {m.docente_nombre} | '
            f'Total sesiones: {dto.total_sesiones} | '
            f'Asistencia grupal: {dto.porcentaje_asistencia_grupal:.1f}%',
            body,
        ),
        Spacer(1, 12),
    ]

    header = ['Matrícula', 'Nombre', 'Presentes', 'Retardos', 'Ausentes', '% Asistencia']
    data = [header]
    for alumno in dto.alumnos:
        data.append(
            [
                alumno.matricula,
                alumno.nombre,
                str(alumno.presentes),
                str(alumno.retardos),
                str(alumno.ausentes),
                f'{alumno.porcentaje_asistencia:.1f}',
            ]
        )

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, -1), font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer
