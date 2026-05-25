import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';

import { PeriodoApiDto } from '../../models/periodos-api.model';
import {
  AgmListPage,
  buildApiUrl,
  buildListPage,
  extractAgmListData,
  extractAgmPagination,
  extractApiErrorMessage,
  unwrapAgmData,
} from '../tools/agm-api.helpers';

export type PeriodoTemporada = 'Primavera' | 'Verano' | 'Otoño';

export interface PeriodoItem {
  id: number;
  nombre: string;
  temporada: PeriodoTemporada;
  anio: number;
  fechaInicio: string;
  fechaFin: string;
  activo: boolean;
  planEstudios: string;
}

export interface PeriodoFormValue {
  temporada: PeriodoTemporada;
  anio: number;
  fechaInicio: string;
  fechaFin: string;
  planEstudios?: string;
  activo?: boolean;
}

export interface PeriodosQuery {
  search?: string;
  temporada?: PeriodoTemporada | 'Todos';
  page?: number;
  pageSize?: number;
}

export type PeriodosPage = AgmListPage<PeriodoItem>;

@Injectable({ providedIn: 'root' })
export class PeriodosService {
  private readonly basePath = 'periodos';

  constructor(private http: HttpClient) {}

  getPeriodos(query: PeriodosQuery = {}): Observable<PeriodosPage> {
    const normalized = this.normalizeQuery(query);
    const needsClientFilter =
      Boolean(normalized.search) || normalized.temporada !== 'Todos';

    const params = new HttpParams({
      fromObject: {
        page: String(needsClientFilter ? 1 : normalized.page),
        limit: String(needsClientFilter ? 100 : normalized.pageSize),
      },
    });

    return this.http
      .get<unknown>(buildApiUrl(`${this.basePath}/`), { params })
      .pipe(
        map((response) => {
          const pagination = extractAgmPagination(response);
          let items = extractAgmListData<PeriodoApiDto>(response).map((dto) =>
            this.mapPeriodo(dto),
          );

          if (needsClientFilter) {
            items = this.filterPeriodos(items, normalized.search, normalized.temporada);
            return this.paginateLocally(items, normalized.page, normalized.pageSize);
          }

          return buildListPage(
            items,
            pagination?.page ?? normalized.page,
            pagination?.limit ?? normalized.pageSize,
            pagination?.total ?? items.length,
          );
        }),
      );
  }

  getPeriodoActivo(): Observable<PeriodoItem | null> {
    return this.http.get<unknown>(buildApiUrl(`${this.basePath}/activo/`)).pipe(
      map((response) => {
        const dto = unwrapAgmData<PeriodoApiDto>(response);
        return dto ? this.mapPeriodo(dto) : null;
      }),
    );
  }

  createPeriodo(periodo: PeriodoFormValue): Observable<PeriodoItem> {
    return this.http
      .post<unknown>(buildApiUrl(`${this.basePath}/`), this.buildPayload(periodo))
      .pipe(map((response) => this.mapPeriodoOrFail(response, 'No se pudo crear el periodo')));
  }

  updatePeriodo(
    periodoId: number,
    periodo: Partial<PeriodoFormValue>,
  ): Observable<PeriodoItem> {
    return this.http
      .put<unknown>(buildApiUrl(`${this.basePath}/${periodoId}/`), this.buildPayload(periodo))
      .pipe(
        map((response) =>
          this.mapPeriodoOrFail(response, 'No se pudo actualizar el periodo'),
        ),
      );
  }

  deletePeriodo(periodoId: number): Observable<void> {
    return this.http.delete<unknown>(buildApiUrl(`${this.basePath}/${periodoId}/`)).pipe(
      map(() => undefined),
    );
  }

  activarPeriodo(periodoId: number): Observable<PeriodoItem> {
    return this.http
      .post<unknown>(buildApiUrl(`${this.basePath}/${periodoId}/activar/`), {})
      .pipe(
        map((response) =>
          this.mapPeriodoOrFail(response, 'No se pudo activar el periodo'),
        ),
      );
  }

  importarMateriasPdf(periodoId: number, archivo: File): Observable<{
    creadas: number;
    actualizadas: number;
    errores: number;
  }> {
    const formData = new FormData();
    formData.append('archivo', archivo, archivo.name);

    return this.http
      .post<unknown>(
        buildApiUrl(`${this.basePath}/${periodoId}/importar-materias/`),
        formData,
      )
      .pipe(
        map((response) => {
          const data = unwrapAgmData<{
            creadas: number;
            actualizadas: number;
            errores: number;
          }>(response);
          if (!data) {
            throw new Error('Respuesta invalida al importar materias');
          }
          return data;
        }),
      );
  }

  static extractError(error: unknown, fallback: string): string {
    return extractApiErrorMessage(error, fallback);
  }

  private mapPeriodoOrFail(response: unknown, fallback: string): PeriodoItem {
    const dto = unwrapAgmData<PeriodoApiDto>(response);
    if (!dto) {
      throw new Error(fallback);
    }
    return this.mapPeriodo(dto);
  }

  private mapPeriodo(dto: PeriodoApiDto): PeriodoItem {
    const nombre = String(dto.nombre ?? '').trim();
    const temporada = this.resolveTemporada(nombre);
    const anio = this.resolveAnio(nombre, dto.fecha_inicio);

    return {
      id: Number(dto.id),
      nombre: nombre || this.buildPeriodoNombre(temporada, anio),
      temporada,
      anio,
      fechaInicio: String(dto.fecha_inicio ?? '').slice(0, 10),
      fechaFin: String(dto.fecha_fin ?? '').slice(0, 10),
      activo: Boolean(dto.activo),
      planEstudios: String(dto.plan_estudios ?? ''),
    };
  }

  private buildPayload(periodo: Partial<PeriodoFormValue>): Record<string, string> {
    const temporada = periodo.temporada ?? 'Primavera';
    const anio = periodo.anio ?? new Date().getFullYear();
    const payload: Record<string, string> = {};

    if (periodo.temporada !== undefined || periodo.anio !== undefined) {
      payload['nombre'] = this.buildPeriodoNombre(temporada, anio);
    }
    if (periodo.fechaInicio) {
      payload['fecha_inicio'] = periodo.fechaInicio;
    }
    if (periodo.fechaFin) {
      payload['fecha_fin'] = periodo.fechaFin;
    }
    if (periodo.planEstudios !== undefined) {
      payload['plan_estudios'] = periodo.planEstudios;
    }

    return payload;
  }

  private normalizeQuery(query: PeriodosQuery): Required<PeriodosQuery> {
    return {
      search: (query.search ?? '').trim(),
      temporada: query.temporada ?? 'Todos',
      page: Math.max(1, query.page ?? 1),
      pageSize: Math.max(1, query.pageSize ?? 10),
    };
  }

  private filterPeriodos(
    items: PeriodoItem[],
    search: string,
    temporada: PeriodoTemporada | 'Todos',
  ): PeriodoItem[] {
    const normalizedSearch = this.normalizeText(search);

    return items.filter((periodo) => {
      const coincideTemporada = temporada === 'Todos' || periodo.temporada === temporada;
      if (!coincideTemporada) {
        return false;
      }
      if (!normalizedSearch) {
        return true;
      }
      const haystack = this.normalizeText(
        [
          periodo.nombre,
          periodo.temporada,
          String(periodo.anio),
          periodo.fechaInicio,
          periodo.fechaFin,
          periodo.planEstudios,
          periodo.activo ? 'activo' : 'inactivo',
        ].join(' '),
      );
      return haystack.includes(normalizedSearch);
    });
  }

  private paginateLocally(
    items: PeriodoItem[],
    page: number,
    pageSize: number,
  ): PeriodosPage {
    const count = items.length;
    const totalPages = Math.max(1, Math.ceil(count / pageSize));
    const safePage = Math.min(page, totalPages);
    const start = (safePage - 1) * pageSize;
    const results = items.slice(start, start + pageSize);
    return buildListPage(results, safePage, pageSize, count);
  }

  private resolveTemporada(nombre: string): PeriodoTemporada {
    const normalized = this.normalizeText(nombre);
    if (normalized.includes('verano')) {
      return 'Verano';
    }
    if (normalized.includes('oton') || normalized.includes('otono')) {
      return 'Otoño';
    }
    return 'Primavera';
  }

  private resolveAnio(nombre: string, fechaInicio?: string): number {
    const fromName = nombre.match(/(19|20)\d{2}/);
    if (fromName) {
      return Number(fromName[0]);
    }
    if (fechaInicio) {
      return new Date(fechaInicio).getFullYear();
    }
    return new Date().getFullYear();
  }

  private buildPeriodoNombre(temporada: PeriodoTemporada, anio: number): string {
    return `${temporada} ${anio}`;
  }

  private normalizeText(value: string): string {
    return value
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase();
  }
}
