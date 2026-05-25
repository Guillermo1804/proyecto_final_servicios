import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';

import {
  AlumnoApiDto,
  ImportarAlumnosPdfResultDto,
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

  getMe(): Observable<AlumnoApiDto> {
    return this.http.get<unknown>(buildApiUrl(`${this.basePath}/me/`)).pipe(
      map((response) => {
        const data = unwrapAgmData<AlumnoApiDto>(response);
        if (!data) {
          throw new Error('Respuesta invalida al consultar perfil de alumno');
        }
        return data;
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

  previewImportarAlumnosPdf(
    materiaId: number,
    file: File,
  ): Observable<ImportarAlumnosPreviewDto> {
    const formData = new FormData();
    formData.append('file', file, file.name);
    formData.append('materia_id', String(materiaId));

    return this.http
      .post<unknown>(buildApiUrl(`${this.basePath}/importar/preview/`), formData)
      .pipe(
        map((response) => {
          const data = unwrapAgmData<ImportarAlumnosPreviewDto>(response);
          if (!data) {
            throw new Error('Respuesta invalida al generar vista previa');
          }
          return data;
        }),
      );
  }

  confirmarImportarAlumnos(
    materiaId: number,
    alumnos: ImportarAlumnosPreviewDto['filas'],
  ): Observable<ImportarAlumnosPdfResultDto> {
    return this.http
      .post<unknown>(buildApiUrl(`${this.basePath}/importar/confirmar/`), {
        materia_id: materiaId,
        alumnos,
      })
      .pipe(
        map((response) => {
          const data = unwrapAgmData<ImportarAlumnosPdfResultDto>(response);
          if (!data) {
            throw new Error('Respuesta invalida al confirmar importacion');
          }
          return data;
        }),
      );
  }

  importarAlumnosPdf(materiaId: number, file: File): Observable<ImportarAlumnosPdfResultDto> {
    const formData = new FormData();
    formData.append('file', file, file.name);
    formData.append('materia_id', String(materiaId));

    return this.http
      .post<unknown>(buildApiUrl(`${this.basePath}/importar/`), formData)
      .pipe(
        map((response) => {
          const data = unwrapAgmData<ImportarAlumnosPdfResultDto>(response);
          if (!data) {
            throw new Error('Respuesta invalida al importar alumnos');
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

  activarAlumno(alumnoId: number): Observable<AlumnoApiDto> {
    return this.http
      .post<unknown>(buildApiUrl(`${this.basePath}/${alumnoId}/activar-usuario/`), {})
      .pipe(
        map((response) => {
          const data = unwrapAgmData<AlumnoApiDto>(response);
          if (!data) {
            throw new Error('Respuesta invalida al activar alumno');
          }
          return data;
        }),
      );
  }

  desactivarAlumno(alumnoId: number): Observable<AlumnoApiDto> {
    return this.http
      .post<unknown>(buildApiUrl(`${this.basePath}/${alumnoId}/desactivar-usuario/`), {})
      .pipe(
        map((response) => {
          const data = unwrapAgmData<AlumnoApiDto>(response);
          if (!data) {
            throw new Error('Respuesta invalida al desactivar alumno');
          }
          return data;
        }),
      );
  }

  static extractError(error: unknown, fallback: string): string {
    return extractApiErrorMessage(error, fallback);
  }

  static mapAlumnoNombre(alumno: AlumnoApiDto): string {
    const apellido = String(alumno.apellido ?? '').trim();
    const nombre = String(alumno.nombre ?? '').trim();
    if (apellido && nombre) {
      return `${apellido}, ${nombre}`;
    }
    if (apellido) {
      return apellido;
    }
    if (nombre) {
      return nombre;
    }
    return '—';
  }

  static inicialesDesdeNombre(nombreCompleto: string): string {
    const partes = nombreCompleto.split(/[\s,]+/).filter(Boolean);
    return partes
      .slice(0, 2)
      .map((p) => p.charAt(0).toUpperCase())
      .join('');
  }
}
