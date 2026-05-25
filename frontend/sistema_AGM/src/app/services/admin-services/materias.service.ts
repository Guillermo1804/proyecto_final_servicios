import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';

import { MateriaApiDto } from '../../models/periodos-api.model';
import {
  AgmListPage,
  buildApiUrl,
  buildListPage,
  extractAgmListData,
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

  getMaterias(query: MateriasQuery = {}): Observable<MateriasPage> {
    const normalized = this.normalizeQuery(query);
    const params: Record<string, string> = {
      page: String(normalized.page),
      limit: String(normalized.pageSize),
    };

    if (normalized.periodoId) {
      params['periodo_id'] = String(normalized.periodoId);
    }

    const search = normalized.search.trim();
    if (search) {
      params['nombre'] = search;
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

        if (search) {
          items = this.filterMaterias(items, search);
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

  private filterMaterias(items: MateriaItem[], search: string): MateriaItem[] {
    const term = search.toLowerCase();
    return items.filter((materia) => {
      const haystack = [
        materia.nrc,
        materia.clave,
        materia.nombre,
        materia.seccion,
        materia.docente,
        materia.salon,
        materia.horarios.map((h) => `${h.dia} ${h.hora}`).join(' '),
      ]
        .join(' ')
        .toLowerCase();
      return haystack.includes(term);
    });
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
