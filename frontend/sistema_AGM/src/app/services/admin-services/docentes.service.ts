import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';

import { DocenteApiDto, ImportarDocentesResultDto } from '../../models/alumnos-api.model';
import {
  AgmListPage,
  buildApiUrl,
  buildListPage,
  extractAgmListData,
  extractApiErrorMessage,
  unwrapAgmData,
} from '../tools/agm-api.helpers';

export type DocenteEstado = 'Activo' | 'Inactivo';

export interface DocenteItem {
  id: number;
  nombre: string;
  correo: string;
  ubicacion: string;
  estado: DocenteEstado;
  usuarioId: number | null;
}

export interface DocentesQuery {
  search?: string;
  page?: number;
  pageSize?: number;
}

export type DocentesPage = AgmListPage<DocenteItem>;

@Injectable({ providedIn: 'root' })
export class DocentesService {
  private readonly basePath = 'docentes';

  constructor(private http: HttpClient) {}

  getDocentes(query: DocentesQuery = {}): Observable<DocentesPage> {
    const normalized = this.normalizeQuery(query);
    const term = normalized.search.trim();
    const needsClientFilter = Boolean(term);

    const params: Record<string, string> = {
      page: String(needsClientFilter ? 1 : normalized.page),
      limit: String(needsClientFilter ? 100 : normalized.pageSize),
    };

    const httpParams = new HttpParams({ fromObject: params });

    return this.http.get<unknown>(buildApiUrl(`${this.basePath}/`), { params: httpParams }).pipe(
      map((response) => {
        const data = unwrapAgmData<{ count?: number; results?: DocenteApiDto[] }>(response);
        const rawList = Array.isArray(data?.results)
          ? data.results
          : extractAgmListData<DocenteApiDto>(response);

        if (needsClientFilter) {
          const filtered = this.filterDocentesFromDto(rawList, term);
          const items = filtered.map((dto) => this.mapDocente(dto));
          return this.paginateLocally(items, normalized.page, normalized.pageSize);
        }

        const items = rawList.map((dto) => this.mapDocente(dto));
        return buildListPage(
          items,
          normalized.page,
          normalized.pageSize,
          Number(data?.count ?? items.length),
        );
      }),
    );
  }

  /** Busca docente vinculado al usuario autenticado (MS-1). */
  findDocenteByUsuarioId(usuarioId: number): Observable<DocenteItem | null> {
    return this.findDocenteApiByUsuarioId(usuarioId).pipe(
      map((dto) => (dto ? this.mapDocente(dto) : null)),
    );
  }

  /** Registro crudo en MS-3 (nombre y apellido por separado). */
  findDocenteApiByUsuarioId(usuarioId: number): Observable<DocenteApiDto | null> {
    const params = new HttpParams({
      fromObject: { usuario_id: String(usuarioId), page: '1', limit: '10' },
    });

    return this.http.get<unknown>(buildApiUrl(`${this.basePath}/`), { params }).pipe(
      map((response) => {
        const data = unwrapAgmData<{ results?: DocenteApiDto[] }>(response);
        const list = Array.isArray(data?.results)
          ? data.results
          : extractAgmListData<DocenteApiDto>(response);
        return list.find((d) => d.usuario_id === usuarioId) ?? list[0] ?? null;
      }),
    );
  }

  deleteDocente(docenteId: number): Observable<void> {
    return this.http
      .delete<unknown>(buildApiUrl(`${this.basePath}/${docenteId}/`))
      .pipe(map(() => undefined));
  }

  activarDocente(docenteId: number): Observable<DocenteItem> {
    return this.http
      .post<unknown>(buildApiUrl(`${this.basePath}/${docenteId}/activar-usuario/`), {})
      .pipe(
        map((response) => {
          const dto = unwrapAgmData<DocenteApiDto>(response);
          if (!dto) {
            throw new Error('Respuesta invalida al activar docente');
          }
          return this.mapDocente(dto);
        }),
      );
  }

  importarDocentesPdf(file: File): Observable<ImportarDocentesResultDto> {
    const formData = new FormData();
    formData.append('file', file, file.name);

    return this.http
      .post<unknown>(buildApiUrl(`${this.basePath}/importar/`), formData)
      .pipe(
        map((response) => {
          const data = unwrapAgmData<ImportarDocentesResultDto>(response);
          if (!data) {
            throw new Error('Respuesta invalida al importar docentes');
          }
          return data;
        }),
      );
  }

  static extractError(error: unknown, fallback: string): string {
    return extractApiErrorMessage(error, fallback);
  }

  private mapDocente(dto: DocenteApiDto): DocenteItem {
    const nombreCompleto = `${dto.nombre} ${dto.apellido}`.trim();
    return {
      id: Number(dto.id),
      nombre: nombreCompleto,
      correo: String(dto.email ?? ''),
      ubicacion: String(dto.departamento ?? 'Sin departamento'),
      estado: dto.usuario_id ? 'Activo' : 'Inactivo',
      usuarioId: dto.usuario_id ?? null,
    };
  }

  private normalizeQuery(query: DocentesQuery): Required<DocentesQuery> {
    return {
      search: query.search ?? '',
      page: Math.max(1, query.page ?? 1),
      pageSize: Math.max(1, query.pageSize ?? 5),
    };
  }

  /** Filtra por coincidencia en cualquier parte del nombre completo, correo o departamento. */
  private filterDocentesFromDto(items: DocenteApiDto[], search: string): DocenteApiDto[] {
    const tokens = this.normalizeText(search).split(/\s+/).filter(Boolean);
    if (!tokens.length) {
      return items;
    }

    return items.filter((dto) => {
      const haystack = this.normalizeText(
        [dto.nombre, dto.apellido, dto.email, dto.departamento].join(' '),
      );
      return tokens.every((token) => haystack.includes(token));
    });
  }

  private paginateLocally(
    items: DocenteItem[],
    page: number,
    pageSize: number,
  ): DocentesPage {
    const count = items.length;
    const totalPages = Math.max(1, Math.ceil(count / pageSize));
    const safePage = Math.min(Math.max(1, page), totalPages);
    const start = (safePage - 1) * pageSize;
    return buildListPage(items.slice(start, start + pageSize), safePage, pageSize, count);
  }

  private normalizeText(value: string): string {
    return value
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase();
  }
}
