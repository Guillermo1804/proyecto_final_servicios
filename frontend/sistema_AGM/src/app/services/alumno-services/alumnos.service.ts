import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';

import {
  AlumnoApiDto,
  ImportarAlumnosConfirmarDto,
  ImportarAlumnosPreviewDto,
  InscripcionMateriaApiDto,
} from '../../models/alumnos-api.model';
import {
  AgmListPage,
  buildApiUrl,
  buildListPage,
  extractAgmListData,
  extractApiErrorMessage,
  unwrapAgmData,
} from '../tools/agm-api.helpers';

@Injectable({ providedIn: 'root' })
export class AlumnosService {
  private readonly basePath = 'alumnos';

  constructor(private http: HttpClient) {}

  getAlumnosPorMateria(
    materiaId: number,
    page = 1,
    pageSize = 50,
  ): Observable<AgmListPage<InscripcionMateriaApiDto>> {
    const params = new HttpParams({
      fromObject: {
        materia_id: String(materiaId),
        page: String(page),
        limit: String(pageSize),
      },
    });

    return this.http
      .get<unknown>(buildApiUrl(`${this.basePath}/por-materia/`), { params })
      .pipe(
        map((response) => {
          const data = unwrapAgmData<{
            count?: number;
            results?: InscripcionMateriaApiDto[];
          }>(response);
          const results = Array.isArray(data?.results)
            ? data.results
            : extractAgmListData<InscripcionMateriaApiDto>(response);
          return buildListPage(
            results,
            page,
            pageSize,
            Number(data?.count ?? results.length),
          );
        }),
      );
  }

  getMeMaterias(page = 1, pageSize = 50): Observable<AgmListPage<InscripcionMateriaApiDto>> {
    const params = new HttpParams({
      fromObject: { page: String(page), limit: String(pageSize) },
    });

    return this.http
      .get<unknown>(buildApiUrl(`${this.basePath}/me/materias/`), { params })
      .pipe(
        map((response) => {
          const data = unwrapAgmData<{
            count?: number;
            results?: InscripcionMateriaApiDto[];
          }>(response);
          const results = Array.isArray(data?.results)
            ? data.results
            : extractAgmListData<InscripcionMateriaApiDto>(response);
          return buildListPage(
            results,
            page,
            pageSize,
            Number(data?.count ?? results.length),
          );
        }),
      );
  }

  importarPreview(archivo: File): Observable<ImportarAlumnosPreviewDto> {
    const formData = new FormData();
    formData.append('archivo', archivo, archivo.name);

    return this.http
      .post<unknown>(buildApiUrl(`${this.basePath}/importar/preview/`), formData)
      .pipe(
        map((response) => {
          const data = unwrapAgmData<ImportarAlumnosPreviewDto>(response);
          if (!data) {
            throw new Error('Respuesta invalida en preview de importacion');
          }
          return data;
        }),
      );
  }

  importarConfirmar(alumnos: Record<string, unknown>[]): Observable<ImportarAlumnosConfirmarDto> {
    return this.http
      .post<unknown>(buildApiUrl(`${this.basePath}/importar/confirmar/`), { alumnos })
      .pipe(
        map((response) => {
          const data = unwrapAgmData<ImportarAlumnosConfirmarDto>(response);
          if (!data) {
            throw new Error('Respuesta invalida al confirmar importacion');
          }
          return data;
        }),
      );
  }

  bajaMateria(alumnoId: number, materiaId: number): Observable<unknown> {
    return this.http
      .post<unknown>(buildApiUrl(`${this.basePath}/${alumnoId}/baja-materia/`), {
        materia_id: materiaId,
      })
      .pipe(map((response) => unwrapAgmData(response)));
  }

  static extractError(error: unknown, fallback: string): string {
    return extractApiErrorMessage(error, fallback);
  }

  static mapAlumnoNombre(alumno: AlumnoApiDto): string {
    return `${alumno.apellido}, ${alumno.nombre}`.trim();
  }

  static inicialesDesdeNombre(nombreCompleto: string): string {
    const partes = nombreCompleto.split(/[\s,]+/).filter(Boolean);
    return partes
      .slice(0, 2)
      .map((p) => p.charAt(0).toUpperCase())
      .join('');
  }
}
