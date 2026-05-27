import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, from, throwError } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';

import {
  EstadisticasDocenteApiDto,
  ReporteDescargaFormato,
  ReporteDescargaTipo,
} from '../models/reportes-api.model';
import { AgmApiResponse } from '../models/auth-api.model';
import { buildApiUrl, extractApiErrorMessage, unwrapAgmData } from './tools/agm-api.helpers';

@Injectable({ providedIn: 'root' })
export class ReportesService {
  constructor(private readonly http: HttpClient) {}

  getEstadisticasDocente(usuarioId: number): Observable<EstadisticasDocenteApiDto> {
    return this.http
      .get<AgmApiResponse<EstadisticasDocenteApiDto>>(
        buildApiUrl(`estadisticas/docente/${usuarioId}`),
      )
      .pipe(
        switchMap((response) => {
          const data = unwrapAgmData<EstadisticasDocenteApiDto>(response);
          if (!data) {
            return throwError(() => new Error('Respuesta de estadísticas vacía (MS-7).'));
          }
          return from([data]);
        }),
        catchError((err) =>
          throwError(() => new Error(extractApiErrorMessage(err, 'No se pudieron cargar estadísticas (MS-7).'))),
        ),
      );
  }

  descargarReporte(
    tipo: ReporteDescargaTipo,
    materiaId: number,
    formato: ReporteDescargaFormato,
  ): Observable<Blob> {
    const params = new HttpParams({ fromObject: { formato } });
    const path =
      tipo === 'calificaciones'
        ? `reportes/calificaciones/${materiaId}`
        : `reportes/asistencias/${materiaId}`;

    return this.http
      .get(buildApiUrl(path), { params, responseType: 'blob' })
      .pipe(catchError((err) => this.failBlob(err, 'No se pudo generar el reporte (MS-7).')));
  }

  private failBlob(err: unknown, fallback: string): Observable<never> {
    if (err instanceof HttpErrorResponse && err.error instanceof Blob) {
      return from(err.error.text()).pipe(
        switchMap((text) => {
          let message = fallback;
          try {
            const body = JSON.parse(text) as { message?: string };
            if (body?.message) {
              message = body.message;
            }
          } catch {
            // Mantener fallback.
          }
          return throwError(() => new Error(message));
        }),
      );
    }
    return throwError(() => new Error(extractApiErrorMessage(err, fallback)));
  }
}
