import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, catchError, map, of, throwError } from 'rxjs';

import {
  ActividadesMateriaDto,
  CalificacionOutputDto,
  ConcentradoMateriaDto,
  ImportarCalificacionesResumenDto,
  PonderacionesMateriaDto,
  ActividadApiDto,
} from '../../models/calificaciones-api.model';
import { buildApiUrl, extractApiErrorMessage, unwrapAgmData } from '../tools/agm-api.helpers';

export interface PonderacionFormItem {
  nombre_categoria: string;
  porcentaje: number;
}

export interface ActividadCreatePayload {
  ponderacion_id: number;
  nombre: string;
  descripcion?: string;
  fecha?: string | null;
}

@Injectable({ providedIn: 'root' })
export class CalificacionesService {
  constructor(private http: HttpClient) {}

  getPonderaciones(materiaId: number): Observable<PonderacionesMateriaDto> {
    return this.http
      .get<unknown>(buildApiUrl(`ponderaciones/${materiaId}`))
      .pipe(
        map((response) => this.requireData<PonderacionesMateriaDto>(response, 'ponderaciones')),
        catchError((error) => {
          if (this.isNotFound(error)) {
            return of({ materia_id: materiaId, ponderaciones: [], total: 0 });
          }
          return throwError(() => error);
        }),
      );
  }

  savePonderaciones(materiaId: number, ponderaciones: PonderacionFormItem[]): Observable<PonderacionesMateriaDto> {
    return this.http
      .post<unknown>(buildApiUrl(`ponderaciones/${materiaId}`), { ponderaciones })
      .pipe(map((response) => this.requireData<PonderacionesMateriaDto>(response, 'ponderaciones')));
  }

  importPonderaciones(materiaId: number, archivo: File): Observable<PonderacionesMateriaDto> {
    const formData = new FormData();
    formData.append('archivo', archivo, archivo.name);
    return this.http
      .post<unknown>(buildApiUrl(`ponderaciones/${materiaId}/importar`), formData)
      .pipe(map((response) => this.requireData<PonderacionesMateriaDto>(response, 'importar ponderaciones')));
  }

  getActividades(materiaId: number): Observable<ActividadesMateriaDto> {
    const params = new HttpParams({ fromObject: { materia: String(materiaId) } });
    return this.http
      .get<unknown>(buildApiUrl('actividades'), { params })
      .pipe(
        map((response) => this.requireData<ActividadesMateriaDto>(response, 'actividades')),
        catchError((error) => {
          if (this.isNotFound(error)) {
            return of({ materia_id: materiaId, categorias: [] });
          }
          return throwError(() => error);
        }),
      );
  }

  createActividad(payload: ActividadCreatePayload): Observable<ActividadApiDto> {
    return this.http
      .post<unknown>(buildApiUrl('actividades'), payload)
      .pipe(map((response) => this.requireData<ActividadApiDto>(response, 'actividad')));
  }

  upsertCalificacion(
    actividadId: number,
    alumnoId: number,
    calificacion: number,
  ): Observable<CalificacionOutputDto> {
    return this.http
      .post<unknown>(buildApiUrl('calificaciones/'), {
        actividad_id: actividadId,
        alumno_id: alumnoId,
        calificacion,
      })
      .pipe(map((response) => this.requireData<CalificacionOutputDto>(response, 'calificacion')));
  }

  importCalificaciones(materiaId: number, archivo: File): Observable<ImportarCalificacionesResumenDto> {
    const formData = new FormData();
    formData.append('archivo', archivo, archivo.name);
    return this.http
      .post<unknown>(buildApiUrl(`calificaciones/importar/${materiaId}`), formData)
      .pipe(
        map((response) =>
          this.requireData<ImportarCalificacionesResumenDto>(response, 'importar calificaciones'),
        ),
      );
  }

  getConcentrado(materiaId: number): Observable<ConcentradoMateriaDto> {
    return this.http
      .get<unknown>(buildApiUrl(`concentrado/${materiaId}`))
      .pipe(
        map((response) => this.requireData<ConcentradoMateriaDto>(response, 'concentrado')),
        catchError((error) => {
          if (this.isNotFound(error)) {
            return of({ materia_id: materiaId, categorias: [], alumnos: [] });
          }
          return throwError(() => error);
        }),
      );
  }

  cerrarMateria(materiaId: number): Observable<{ materia_id: number; cerrada: boolean }> {
    return this.http
      .post<unknown>(buildApiUrl(`materias/${materiaId}/cerrar`), {})
      .pipe(
        map((response) =>
          this.requireData<{ materia_id: number; cerrada: boolean }>(response, 'cerrar materia'),
        ),
      );
  }

  imprimirLista(materiaId: number): Observable<{ materia_id: number; lista_impresa: boolean }> {
    return this.http
      .post<unknown>(buildApiUrl(`materias/${materiaId}/imprimir-lista`), {})
      .pipe(
        map((response) =>
          this.requireData<{ materia_id: number; lista_impresa: boolean }>(
            response,
            'imprimir lista',
          ),
        ),
      );
  }

  mapApiError(error: unknown, fallback: string): string {
    return extractApiErrorMessage(error, fallback);
  }

  private requireData<T>(response: unknown, context: string): T {
    const data = unwrapAgmData<T>(response);
    if (data === null || data === undefined) {
      throw new Error(`Respuesta invalida al obtener ${context}`);
    }
    return data;
  }

  private isNotFound(error: unknown): boolean {
    return Boolean(
      error &&
        typeof error === 'object' &&
        'status' in error &&
        Number((error as { status?: number }).status) === 404,
    );
  }
}
