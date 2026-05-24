import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, map, Observable, of } from 'rxjs';

import { environment } from '../../../environments/environment';

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

export interface PeriodosPage {
  results: PeriodoItem[];
  count: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

@Injectable({
  providedIn: 'root'
})
export class PeriodosService {

  private readonly periodosApiUrl = '/periodos/';
  private readonly periodosCache: PeriodoItem[] = [
    {
      id: 1,
      nombre: 'Primavera 2026',
      temporada: 'Primavera',
      anio: 2026,
      fechaInicio: '2026-02-01',
      fechaFin: '2026-06-30',
      activo: true,
      planEstudios: 'Plan 2021'
    },
    {
      id: 2,
      nombre: 'Verano 2026',
      temporada: 'Verano',
      anio: 2026,
      fechaInicio: '2026-07-08',
      fechaFin: '2026-08-21',
      activo: false,
      planEstudios: 'Plan 2021'
    },
    {
      id: 3,
      nombre: 'Otoño 2026',
      temporada: 'Otoño',
      anio: 2026,
      fechaInicio: '2026-09-01',
      fechaFin: '2026-12-18',
      activo: false,
      planEstudios: 'Plan 2021'
    },
    {
      id: 4,
      nombre: 'Primavera 2025',
      temporada: 'Primavera',
      anio: 2025,
      fechaInicio: '2025-02-03',
      fechaFin: '2025-06-27',
      activo: false,
      planEstudios: 'Plan 2021'
    },
    {
      id: 5,
      nombre: 'Verano 2025',
      temporada: 'Verano',
      anio: 2025,
      fechaInicio: '2025-07-07',
      fechaFin: '2025-08-22',
      activo: false,
      planEstudios: 'Plan 2021'
    },
    {
      id: 6,
      nombre: 'Otoño 2025',
      temporada: 'Otoño',
      anio: 2025,
      fechaInicio: '2025-09-01',
      fechaFin: '2025-12-19',
      activo: false,
      planEstudios: 'Plan 2021'
    }
  ];

  constructor(private http: HttpClient) {}

  getPeriodos(query: PeriodosQuery = {}): Observable<PeriodosPage> {
    const normalizedQuery = this.normalizeQuery(query);
    const paramsObject: Record<string, string> = {
      search: normalizedQuery.search,
      page: String(normalizedQuery.page),
      limit: String(normalizedQuery.pageSize)
    };

    if (normalizedQuery.temporada !== 'Todos') {
      paramsObject['temporada'] = normalizedQuery.temporada;
    }

    const httpParams = new HttpParams({
      fromObject: paramsObject
    });

    return this.http.get<unknown>(this.buildApiUrl(this.periodosApiUrl), { params: httpParams }).pipe(
      map((response) => this.normalizeResponse(response, normalizedQuery)),
      catchError(() => of(this.getLocalPage(normalizedQuery)))
    );
  }

  getPeriodoActivo(): Observable<PeriodoItem | null> {
    return this.http.get<unknown>(this.buildApiUrl('/periodos/activo')).pipe(
      map((response) => this.normalizePeriodo(response)),
      catchError(() => of(this.periodosCache.find((periodo) => periodo.activo) ?? null))
    );
  }

  createPeriodo(periodo: PeriodoFormValue): Observable<PeriodoItem | null> {
    const payload = this.buildPayload(periodo);

    return this.http.post<unknown>(this.buildApiUrl(this.periodosApiUrl), payload).pipe(
      map((response) => {
        const normalized = this.normalizePeriodo(response);

        if (normalized) {
          return this.upsertLocalPeriodo(normalized);
        }

        return this.upsertLocalPeriodo(this.createLocalPeriodo(payload));
      }),
      catchError(() => of(this.upsertLocalPeriodo(this.createLocalPeriodo(payload))))
    );
  }

  updatePeriodo(periodoId: number, periodo: Partial<PeriodoFormValue>): Observable<PeriodoItem | null> {
    const payload = this.buildPayload(periodo, false);

    return this.http.put<unknown>(this.buildApiUrl(`${this.periodosApiUrl}${periodoId}/`), payload).pipe(
      map((response) => {
        const normalized = this.normalizePeriodo(response);

        if (normalized) {
          return this.upsertLocalPeriodo({ ...normalized, id: periodoId });
        }

        return this.upsertLocalPeriodo(this.updateLocalPeriodo(periodoId, payload));
      }),
      catchError(() => of(this.upsertLocalPeriodo(this.updateLocalPeriodo(periodoId, payload))))
    );
  }

  deletePeriodo(periodoId: number): Observable<boolean> {
    return this.http.delete<void>(this.buildApiUrl(`${this.periodosApiUrl}${periodoId}/`)).pipe(
      map(() => true),
      catchError(() => of(this.deleteLocalPeriodo(periodoId)))
    );
  }

  activarPeriodo(periodoId: number): Observable<PeriodoItem | null> {
    return this.http.post<unknown>(this.buildApiUrl(`${this.periodosApiUrl}${periodoId}/activar`), {}).pipe(
      map((response) => {
        const normalized = this.normalizePeriodo(response);

        if (normalized) {
          return this.upsertLocalPeriodo({ ...normalized, activo: true, id: periodoId });
        }

        return this.setLocalPeriodoActivo(periodoId, true);
      }),
      catchError(() => of(this.setLocalPeriodoActivo(periodoId, true)))
    );
  }

  desactivarPeriodo(periodoId: number): Observable<PeriodoItem | null> {
    return this.http.put<unknown>(this.buildApiUrl(`${this.periodosApiUrl}${periodoId}/`), { activo: false }).pipe(
      map((response) => {
        const normalized = this.normalizePeriodo(response);

        if (normalized) {
          return this.upsertLocalPeriodo({ ...normalized, activo: false, id: periodoId });
        }

        return this.setLocalPeriodoActivo(periodoId, false);
      }),
      catchError(() => of(this.setLocalPeriodoActivo(periodoId, false)))
    );
  }

  private buildApiUrl(path: string): string {
    const baseUrl = environment.apiBaseUrl || environment.url_api || '';

    return `${baseUrl.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
  }

  private normalizeQuery(query: PeriodosQuery): Required<PeriodosQuery> {
    return {
      search: (query.search ?? '').trim(),
      temporada: query.temporada ?? 'Todos',
      page: Math.max(1, query.page ?? 1),
      pageSize: Math.max(1, query.pageSize ?? 10)
    };
  }

  private normalizeResponse(response: unknown, query: Required<PeriodosQuery>): PeriodosPage {
    if (Array.isArray(response)) {
      return this.buildPage(response.map((item) => this.normalizePeriodo(item)).filter((item): item is PeriodoItem => Boolean(item)), query);
    }

    if (response && typeof response === 'object') {
      const payload = response as Record<string, any>;
      const nestedResults = this.extractResults(payload);

      if (nestedResults) {
        const normalizedResults = nestedResults
          .map((item) => this.normalizePeriodo(item))
          .filter((item): item is PeriodoItem => Boolean(item));

        return this.buildPage(normalizedResults, {
          search: query.search,
          temporada: query.temporada,
          page: Number(payload['page'] ?? query.page) || query.page,
          pageSize: Number(payload['pageSize'] ?? payload['page_size'] ?? payload['limit'] ?? query.pageSize) || query.pageSize
        }, Number(payload['count'] ?? payload['total'] ?? normalizedResults.length) || normalizedResults.length, false);
      }
    }

    return this.getLocalPage(query);
  }

  private extractResults(payload: Record<string, any>): PeriodoItem[] | null {
    const candidates = [payload['results'], payload['data'], payload['items'], payload['periodos']];

    for (const candidate of candidates) {
      if (Array.isArray(candidate)) {
        return candidate as PeriodoItem[];
      }

      if (candidate && typeof candidate === 'object' && Array.isArray(candidate.results)) {
        return candidate.results as PeriodoItem[];
      }
    }

    return null;
  }

  private getLocalPage(query: Required<PeriodosQuery>): PeriodosPage {
    const filtered = this.filterLocalPeriodos(query.search, query.temporada);
    return this.buildPage(filtered, query, filtered.length, true);
  }

  private buildPage(items: PeriodoItem[], query: Required<PeriodosQuery>, totalOverride?: number, shouldSlice = true): PeriodosPage {
    const count = totalOverride ?? items.length;
    const totalPages = Math.max(1, Math.ceil(count / query.pageSize));
    const page = Math.min(query.page, totalPages);
    const results = shouldSlice
      ? items.slice((page - 1) * query.pageSize, (page - 1) * query.pageSize + query.pageSize)
      : items;

    return {
      results,
      count,
      page,
      pageSize: query.pageSize,
      totalPages
    };
  }

  private filterLocalPeriodos(search: string, temporada: PeriodoTemporada | 'Todos'): PeriodoItem[] {
    const normalizedSearch = this.normalizeText(search);

    return this.periodosCache.filter((periodo) => {
      const coincideTemporada = temporada === 'Todos' || periodo.temporada === temporada;

      if (!coincideTemporada) {
        return false;
      }

      if (!normalizedSearch) {
        return true;
      }

      const haystack = this.normalizeText([
        periodo.nombre,
        periodo.temporada,
        String(periodo.anio),
        periodo.fechaInicio,
        periodo.fechaFin,
        periodo.planEstudios,
        periodo.activo ? 'activo' : 'inactivo'
      ].join(' '));

      return haystack.includes(normalizedSearch);
    });
  }

  private normalizePeriodo(value: unknown): PeriodoItem | null {
    if (!value || typeof value !== 'object') {
      return null;
    }

    const payload = value as Record<string, any>;
    const nombre = String(payload['nombre'] ?? payload['name'] ?? '').trim();
    const temporada = this.resolveTemporada(payload['temporada'] ?? payload['season'] ?? nombre);
    const anio = this.resolveAnio(payload['anio'] ?? payload['year'] ?? nombre);
    const fechaInicio = String(payload['fechaInicio'] ?? payload['fecha_inicio'] ?? payload['start_date'] ?? '').slice(0, 10);
    const fechaFin = String(payload['fechaFin'] ?? payload['fecha_fin'] ?? payload['end_date'] ?? '').slice(0, 10);
    const activo = this.resolveActivo(payload);
    const planEstudios = String(payload['planEstudios'] ?? payload['plan_estudios'] ?? 'Plan 2021');

    if (!nombre && !temporada) {
      return null;
    }

    return {
      id: Number(payload['id'] ?? payload['pk'] ?? 0) || this.siguienteId(),
      nombre: nombre || this.buildPeriodoNombre(temporada, anio),
      temporada,
      anio,
      fechaInicio,
      fechaFin,
      activo,
      planEstudios
    };
  }

  private buildPayload(periodo: Partial<PeriodoFormValue>, includeActvo = true): Record<string, any> {
    const temporada = periodo.temporada ?? 'Primavera';
    const anio = periodo.anio ?? new Date().getFullYear();

    return {
      nombre: this.buildPeriodoNombre(temporada, anio),
      temporada,
      anio,
      fecha_inicio: periodo.fechaInicio ?? '',
      fecha_fin: periodo.fechaFin ?? '',
      plan_estudios: periodo.planEstudios ?? `Plan ${anio}`,
      ...(includeActvo ? { activo: periodo.activo ?? false } : {})
    };
  }

  private createLocalPeriodo(payload: Record<string, any>): PeriodoItem {
    const periodo: PeriodoItem = {
      id: this.siguienteId(),
      nombre: String(payload['nombre']),
      temporada: payload['temporada'],
      anio: Number(payload['anio']),
      fechaInicio: String(payload['fecha_inicio'] ?? payload['fechaInicio']),
      fechaFin: String(payload['fecha_fin'] ?? payload['fechaFin']),
      activo: Boolean(payload['activo']),
      planEstudios: String(payload['plan_estudios'] ?? payload['planEstudios'] ?? `Plan ${payload['anio']}`)
    };

    return this.upsertLocalPeriodo(periodo);
  }

  private updateLocalPeriodo(periodoId: number, payload: Record<string, any>): PeriodoItem {
    const existing = this.periodosCache.find((item) => item.id === periodoId);

    if (!existing) {
      return this.createLocalPeriodo(payload);
    }

    const updated: PeriodoItem = {
      ...existing,
      nombre: String(payload['nombre'] ?? existing.nombre),
      temporada: (payload['temporada'] ?? existing.temporada) as PeriodoTemporada,
      anio: Number(payload['anio'] ?? existing.anio),
      fechaInicio: String(payload['fecha_inicio'] ?? payload['fechaInicio'] ?? existing.fechaInicio),
      fechaFin: String(payload['fecha_fin'] ?? payload['fechaFin'] ?? existing.fechaFin),
      activo: payload['activo'] !== undefined ? Boolean(payload['activo']) : existing.activo,
      planEstudios: String(payload['plan_estudios'] ?? payload['planEstudios'] ?? existing.planEstudios)
    };

    return this.upsertLocalPeriodo(updated);
  }

  private upsertLocalPeriodo(periodo: PeriodoItem): PeriodoItem {
    if (periodo.activo) {
      this.periodosCache.forEach((item) => {
        item.activo = item.id === periodo.id;
      });
    }

    const index = this.periodosCache.findIndex((item) => item.id === periodo.id);

    if (index === -1) {
      this.periodosCache.unshift({ ...periodo });
      return periodo;
    }

    this.periodosCache[index] = { ...this.periodosCache[index], ...periodo };
    return { ...this.periodosCache[index] };
  }

  private setLocalPeriodoActivo(periodoId: number, activo: boolean): PeriodoItem | null {
    const periodo = this.periodosCache.find((item) => item.id === periodoId);

    if (!periodo) {
      return null;
    }

    if (activo) {
      this.periodosCache.forEach((item) => {
        item.activo = item.id === periodoId;
      });
    } else {
      periodo.activo = false;
    }

    return { ...periodo };
  }

  private deleteLocalPeriodo(periodoId: number): boolean {
    const index = this.periodosCache.findIndex((item) => item.id === periodoId);

    if (index === -1) {
      return false;
    }

    this.periodosCache.splice(index, 1);
    return true;
  }

  private resolveTemporada(value: unknown): PeriodoTemporada {
    const normalized = this.normalizeText(String(value ?? ''));

    if (normalized.includes('verano')) {
      return 'Verano';
    }

    if (normalized.includes('oton') || normalized.includes('otoño')) {
      return 'Otoño';
    }

    return 'Primavera';
  }

  private resolveAnio(value: unknown): number {
    if (typeof value === 'number' && Number.isFinite(value)) {
      return value;
    }

    const extracted = String(value ?? '').match(/(19|20)\d{2}/);

    return extracted ? Number(extracted[0]) : new Date().getFullYear();
  }

  private resolveActivo(payload: Record<string, any>): boolean {
    if (typeof payload['activo'] === 'boolean') {
      return payload['activo'];
    }

    if (typeof payload['estado'] === 'string') {
      return this.normalizeText(payload['estado']) === 'activo';
    }

    return false;
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

  private siguienteId(): number {
    return this.periodosCache.length ? Math.max(...this.periodosCache.map((periodo) => periodo.id)) + 1 : 1;
  }
}