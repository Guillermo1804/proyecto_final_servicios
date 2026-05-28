import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';

import { MateriaApiDto } from '../../models/periodos-api.model';
import {
  AgmListPage,
  buildApiUrl,
  buildListPage,
  extractAgmListData,
  extractApiErrorMessage,
  unwrapAgmData,
} from '../tools/agm-api.helpers';

export interface MateriaHorario {
  dia: string;
  hora: string;
}

export interface MateriaItem {
  id: number;
  periodoId: number;
  nrc: string;
  clave: string;
  nombre: string;
  seccion: string;
  docente: string;
  horarios: MateriaHorario[];
  salon: string;
}

export interface MateriasQuery {
  search?: string;
  page?: number;
  pageSize?: number;
  periodoId?: number;
}

export type MateriasPage = AgmListPage<MateriaItem>;

@Injectable({ providedIn: 'root' })
export class MateriasService {
  private readonly basePath = 'materias';

  constructor(private http: HttpClient) {}

  countByPeriodo(periodoId: number): Observable<number> {
    return this.getMaterias({ periodoId, page: 1, pageSize: 1 }).pipe(
      map((page) => page.count),
    );
  }

  deleteMateria(materiaId: number): Observable<void> {
    return this.http.delete<unknown>(buildApiUrl(`${this.basePath}/${materiaId}/`)).pipe(
      map((response) => {
        if (response && typeof response === 'object' && 'success' in response) {
          const envelope = response as { success?: boolean; message?: string };
          if (envelope.success === false) {
            throw new Error(envelope.message || 'No se pudo eliminar la materia');
          }
        }
        return undefined;
      }),
    );
  }

  static extractError(error: unknown, fallback: string): string {
    return extractApiErrorMessage(error, fallback);
  }

  getMaterias(query: MateriasQuery = {}): Observable<MateriasPage> {
    const normalized = this.normalizeQuery(query);
    const search = normalized.search.trim();
    const needsClientFilter = Boolean(search);

    const params: Record<string, string> = {
      page: String(needsClientFilter ? 1 : normalized.page),
      limit: String(needsClientFilter ? 200 : normalized.pageSize),
    };

    if (normalized.periodoId) {
      params['periodo_id'] = String(normalized.periodoId);
    }

    const httpParams = new HttpParams({ fromObject: params });

    return this.http.get<unknown>(buildApiUrl(`${this.basePath}/`), { params: httpParams }).pipe(
      map((response) => {
        const data = unwrapAgmData<{
          count?: number;
          results?: MateriaApiDto[];
        }>(response);

        const rawList = Array.isArray(data?.results)
          ? data.results
          : extractAgmListData<MateriaApiDto>(response);

        let items = rawList.map((dto) => this.mapMateria(dto));

        if (needsClientFilter) {
          items = this.filterMateriasPorNrcONombre(items, search);
          return this.paginateLocally(items, normalized.page, normalized.pageSize);
        }

        const count = Number(data?.count ?? items.length);
        return buildListPage(
          items,
          normalized.page,
          normalized.pageSize,
          count,
        );
      }),
    );
  }

  private mapMateria(dto: MateriaApiDto): MateriaItem {
    const { horarios, salon } = this.parseHorario(String(dto.horario ?? ''));

    return {
      id: Number(dto.id),
      periodoId: Number(dto.periodo),
      nrc: String(dto.nrc ?? ''),
      clave: String(dto.clave ?? ''),
      nombre: String(dto.nombre ?? ''),
      seccion: String(dto.seccion ?? ''),
      docente: String(dto.docente_nombre ?? '').trim() || 'Sin asignar',
      horarios,
      salon,
    };
  }

  private parseHorario(horario: string): { horarios: MateriaHorario[]; salon: string } {
    const raw = horario.trim();
    if (!raw) {
      return { horarios: [], salon: '—' };
    }

    const segments = raw.split(/[,;|]/).map((part) => part.trim()).filter(Boolean);
    const horarios: MateriaHorario[] = [];
    let salon = '—';

    for (const segment of segments) {
      const salonMatch = segment.match(/\b(\d[A-Z]{2,}\d?\/\d{2,}|[A-Z]-\d{2,}|Lab\.?\s*\d+)\b/i);
      if (salonMatch && salon === '—') {
        salon = salonMatch[1];
      }

      const dayHour = segment.match(/^([LMAJVSD]+)\s+(.+)$/i);
      if (dayHour) {
        horarios.push({ dia: dayHour[1].toUpperCase(), hora: dayHour[2].trim() });
        continue;
      }

      horarios.push({ dia: '—', hora: segment });
    }

    if (!horarios.length) {
      horarios.push({ dia: '—', hora: raw });
    }

    return { horarios, salon };
  }

  private filterMateriasPorNrcONombre(items: MateriaItem[], search: string): MateriaItem[] {
    const term = search.trim().toLowerCase();
    if (!term) {
      return items;
    }

    return items.filter(
      (materia) =>
        materia.nrc.toLowerCase().includes(term) ||
        materia.nombre.toLowerCase().includes(term),
    );
  }

  private paginateLocally(
    items: MateriaItem[],
    page: number,
    pageSize: number,
  ): MateriasPage {
    const count = items.length;
    const totalPages = Math.max(1, Math.ceil(count / pageSize));
    const safePage = Math.min(Math.max(1, page), totalPages);
    const start = (safePage - 1) * pageSize;
    return buildListPage(items.slice(start, start + pageSize), safePage, pageSize, count);
  }

  private normalizeQuery(query: MateriasQuery): {
    search: string;
    page: number;
    pageSize: number;
    periodoId?: number;
  } {
    return {
      search: query.search ?? '',
      page: Math.max(1, query.page ?? 1),
      pageSize: Math.max(1, query.pageSize ?? 5),
      ...(query.periodoId !== undefined ? { periodoId: query.periodoId } : {}),
    };
  }
}
