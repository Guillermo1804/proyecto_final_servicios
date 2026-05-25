import { Injectable } from '@angular/core';
import { Observable, map, of, switchMap } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { AlumnosService } from '../alumno-services/alumnos.service';
import { CalificacionesService } from './calificaciones.service';
import { MateriasDocenteService } from './materias-docente.service';

export interface RendimientoEstudianteItem {
  iniciales: string;
  nombre: string;
  matricula: string;
  promedio: number;
  asistencia: string;
}

@Injectable({ providedIn: 'root' })
export class RendimientoDocenteService {
  readonly pageSizeDefault = 10;
  readonly umbralRiesgo = 7;

  constructor(
    private materiasDocente: MateriasDocenteService,
    private calificaciones: CalificacionesService,
    private alumnos: AlumnosService,
  ) {}

  loadEstudiantesRiesgoPorNrc(nrc: string): Observable<RendimientoEstudianteItem[]> {
    return this.materiasDocente.findMateriaByNrcForImport(nrc).pipe(
      switchMap((materia) => {
        if (!materia?.id) {
          return of([]);
        }
        return this.calificaciones.getConcentrado(materia.id).pipe(
          map((concentrado) => {
            const rows = concentrado?.alumnos ?? [];
            return rows
              .filter((row) => (Number(row.promedio_redondeado) || 0) < this.umbralRiesgo)
              .map((row) => ({
                iniciales: AlumnosService.inicialesDesdeNombre(row.nombre),
                nombre: row.nombre,
                matricula: row.matricula,
                promedio: Number(row.promedio_redondeado) || 0,
                asistencia: '—',
              }))
              .sort((a, b) => a.promedio - b.promedio);
          }),
          catchError(() =>
            this.alumnos.getAlumnosPorMateria(materia.id, 1, 100).pipe(
              map((page) =>
                page.results.map((inscripcion) => {
                  const nombre = AlumnosService.mapAlumnoNombre(inscripcion.alumno);
                  return {
                    iniciales: AlumnosService.inicialesDesdeNombre(nombre),
                    nombre,
                    matricula: inscripcion.alumno.matricula,
                    promedio: 0,
                    asistencia: '—',
                  };
                }),
              ),
            ),
          ),
        );
      }),
    );
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
    const lines = rows.map((row) =>
      [
        this.escapeCsvValue(row.nombre),
        this.escapeCsvValue(row.matricula),
        this.escapeCsvValue(row.promedio.toFixed(1)),
        this.escapeCsvValue(row.asistencia),
      ].join(','),
    );
    return [header.join(','), ...lines].join('\r\n');
  }

  buildPdfHtml(options: {
    title: string;
    subtitle: string;
    rows: RendimientoEstudianteItem[];
    summary: string;
  }): string {
    const rowsHtml = options.rows
      .map(
        (row) => `
      <tr>
        <td>${this.escapeHtml(row.nombre)}</td>
        <td>${this.escapeHtml(row.matricula)}</td>
        <td>${row.promedio.toFixed(1)}</td>
        <td>${this.escapeHtml(row.asistencia)}</td>
      </tr>
    `,
      )
      .join('');

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
    <tbody>${rowsHtml}</tbody>
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
