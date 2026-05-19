"""Generación de bytes de reporte (compartido REST y gRPC)."""

from apps.reportes.dto.report_dto import AsistenciasReportDTO, CalificacionesReportDTO
from apps.reportes.services import excel_generator, pdf_generator

VALID_TIPOS = frozenset({'calificaciones', 'asistencias'})


def normalize_formato(raw: str | None) -> str:
    fmt = (raw or 'xlsx').lower().strip()
    if fmt == 'xls':
        return 'xlsx'
    if fmt in ('xlsx', 'pdf'):
        return fmt
    raise ValueError('formato inválido; use xlsx, xls o pdf')


def normalize_tipo(raw: str | None) -> str:
    tipo = (raw or '').lower().strip()
    if tipo not in VALID_TIPOS:
        raise ValueError('tipo inválido; use calificaciones o asistencias')
    return tipo


def build_report_bytes(
    dto: CalificacionesReportDTO | AsistenciasReportDTO,
    *,
    prefix: str,
    formato: str,
) -> tuple[bytes, str, str]:
    """Retorna (contenido, filename, content_type)."""
    nrc = dto.materia.nrc.replace(' ', '_') or str(dto.materia.materia_id)
    if formato == 'pdf':
        if isinstance(dto, CalificacionesReportDTO):
            buffer = pdf_generator.build_calificaciones_pdf(dto)
        else:
            buffer = pdf_generator.build_asistencias_pdf(dto)
        return (
            buffer.getvalue(),
            f'{prefix}_{nrc}.pdf',
            'application/pdf',
        )
    if isinstance(dto, CalificacionesReportDTO):
        buffer = excel_generator.build_calificaciones_xlsx(dto)
    else:
        buffer = excel_generator.build_asistencias_xlsx(dto)
    return (
        buffer.getvalue(),
        f'{prefix}_{nrc}.xlsx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
