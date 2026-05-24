import { Injectable } from '@angular/core';

export interface RendimientoEstudianteItem {
  iniciales: string;
  nombre: string;
  matricula: string;
  promedio: number;
  asistencia: string;
}

@Injectable({
  providedIn: 'root'
})
export class RendimientoDocenteService {

  readonly pageSizeDefault = 2;

  private readonly estudiantesRiesgo: RendimientoEstudianteItem[] = [
    {
      iniciales: 'LM',
      nombre: 'Lucía Méndez',
      matricula: '20210452',
      promedio: 58.5,
      asistencia: '72%'
    },
    {
      iniciales: 'RG',
      nombre: 'Roberto Gómez',
      matricula: '20210981',
      promedio: 62.0,
      asistencia: '85%'
    },
    {
      iniciales: 'SF',
      nombre: 'Sofía Figueroa',
      matricula: '20220110',
      promedio: 64.5,
      asistencia: '60%'
    },
    {
      iniciales: 'DV',
      nombre: 'Daniel Vera',
      matricula: '20210622',
      promedio: 68.0,
      asistencia: '92%'
    }
  ];

  getEstudiantesRiesgo(): RendimientoEstudianteItem[] {
    return this.estudiantesRiesgo.map((estudiante) => ({ ...estudiante }));
  }

  getTotalPages(totalItems: number, pageSize: number): number {
    return Math.max(1, Math.ceil(totalItems / Math.max(1, pageSize)));
  }

  getPage<T>(items: T[], page: number, pageSize: number): T[] {
    const normalizedPage = Math.max(1, page);
    const normalizedPageSize = Math.max(1, pageSize);
    const startIndex = (normalizedPage - 1) * normalizedPageSize;

    return items.slice(startIndex, startIndex + normalizedPageSize);
  }

  buildCsv(rows: RendimientoEstudianteItem[]): string {
    const header = ['Estudiante', 'Matrícula', 'Promedio', 'Asistencia'];
    const lines = rows.map((row) => [
      this.escapeCsvValue(row.nombre),
      this.escapeCsvValue(row.matricula),
      this.escapeCsvValue(row.promedio.toFixed(1)),
      this.escapeCsvValue(row.asistencia)
    ].join(','));

    return [header.join(','), ...lines].join('\r\n');
  }

  buildPdfHtml(options: { title: string; subtitle: string; rows: RendimientoEstudianteItem[]; summary: string }): string {
    const rowsHtml = options.rows.map((row) => `
      <tr>
        <td>${this.escapeHtml(row.nombre)}</td>
        <td>${this.escapeHtml(row.matricula)}</td>
        <td>${row.promedio.toFixed(1)}</td>
        <td>${this.escapeHtml(row.asistencia)}</td>
      </tr>
    `).join('');

    return `<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>${this.escapeHtml(options.title)}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 32px; color: #111827; }
    h1 { margin: 0 0 8px; font-size: 22px; }
    p { margin: 0 0 16px; color: #4b5563; }
    .summary { margin: 0 0 18px; padding: 12px 14px; background: #f3f4f6; border-radius: 8px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 10px 12px; border-bottom: 1px solid #d1d5db; text-align: left; }
    th { background: #f9fafb; }
  </style>
</head>
<body>
  <h1>${this.escapeHtml(options.title)}</h1>
  <p>${this.escapeHtml(options.subtitle)}</p>
  <div class="summary">${this.escapeHtml(options.summary)}</div>
  <table>
    <thead>
      <tr>
        <th>Estudiante</th>
        <th>Matrícula</th>
        <th>Promedio</th>
        <th>Asistencia</th>
      </tr>
    </thead>
    <tbody>
      ${rowsHtml}
    </tbody>
  </table>
</body>
</html>`;
  }

  private escapeCsvValue(value: string): string {
    const escaped = value.replace(/"/g, '""');

    return /[",\n]/.test(escaped) ? `"${escaped}"` : escaped;
  }

  private escapeHtml(value: string): string {
    return value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
}