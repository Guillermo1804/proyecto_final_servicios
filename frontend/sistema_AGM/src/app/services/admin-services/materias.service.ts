import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, map, Observable, of } from 'rxjs';

import { environment } from '../../../environments/environment';

export interface MateriaHorario {
  dia: string;
  hora: string;
}

export interface MateriaItem {
  id: number;
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
}

export interface MateriasPage {
  results: MateriaItem[];
  count: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

@Injectable({
  providedIn: 'root'
})
export class MateriasService {

  private readonly materiasApiUrl = '/materias/';
  private readonly materiasCache: MateriaItem[] = [
    {
      id: 1,
      nrc: '50030',
      clave: 'CCOS 260',
      nombre: 'Redes de Computadoras',
      seccion: '001',
      docente: 'TREVINO - SANCHEZ DANIEL',
      horarios: [
        { dia: 'L', hora: '10:00 - 10:59' },
        { dia: 'A', hora: '09:00 - 10:59' },
        { dia: 'M', hora: '09:00 - 10:59' }
      ],
      salon: '1CCO4/305'
    },
    {
      id: 2,
      nrc: '50031',
      clave: 'CCOS 261',
      nombre: 'Sistemas Operativos',
      seccion: '001',
      docente: 'TREVIÑO - SANCHEZ DANIEL',
      horarios: [
        { dia: 'L', hora: '11:00 - 11:59' },
        { dia: 'M', hora: '10:00 - 11:59' },
        { dia: 'J', hora: '10:00 - 11:59' }
      ],
      salon: '1CCO4/302'
    },
    {
      id: 3,
      nrc: '50112',
      clave: 'CCOS 262',
      nombre: 'Estructura de Datos',
      seccion: '002',
      docente: 'MTRA. ARIAS LOPEZ KARLA',
      horarios: [
        { dia: 'L', hora: '09:00 - 09:59' },
        { dia: 'A', hora: '09:00 - 10:59' },
        { dia: 'V', hora: '09:00 - 10:59' }
      ],
      salon: '1CCO4/210'
    },
    {
      id: 4,
      nrc: '50113',
      clave: 'MAT 205',
      nombre: 'Cálculo Diferencial',
      seccion: '002',
      docente: 'DR. LUIS GARCIA',
      horarios: [
        { dia: 'M', hora: '10:00 - 11:59' },
        { dia: 'J', hora: '10:00 - 11:59' }
      ],
      salon: 'B-110'
    },
    {
      id: 5,
      nrc: '50224',
      clave: 'FIS 102',
      nombre: 'Física General II',
      seccion: '001',
      docente: 'ING. CARLA RUIZ',
      horarios: [
        { dia: 'L', hora: '12:00 - 12:59' },
        { dia: 'M', hora: '12:00 - 12:59' },
        { dia: 'V', hora: '12:00 - 12:59' }
      ],
      salon: 'Laboratorio 3'
    },
    {
      id: 6,
      nrc: '50225',
      clave: 'HIS 301',
      nombre: 'Historia Universal Moderna',
      seccion: '003',
      docente: 'LIC. SOFÍA RAMÍREZ',
      horarios: [
        { dia: 'S', hora: '09:00 - 11:00' }
      ],
      salon: 'C-018'
    },
    {
      id: 7,
      nrc: '50310',
      clave: 'ADM 110',
      nombre: 'Administración General',
      seccion: '001',
      docente: 'MTRO. RENÉ SALAZAR',
      horarios: [
        { dia: 'L', hora: '08:00 - 09:59' },
        { dia: 'J', hora: '08:00 - 09:59' }
      ],
      salon: 'D-101'
    },
    {
      id: 8,
      nrc: '50311',
      clave: 'ING 220',
      nombre: 'Inglés Intermedio',
      seccion: '004',
      docente: 'MTRA. ELENA TORRES',
      horarios: [
        { dia: 'M', hora: '13:00 - 14:59' },
        { dia: 'V', hora: '13:00 - 14:59' }
      ],
      salon: 'A-009'
    },
    {
      id: 9,
      nrc: '50312',
      clave: 'PRO 330',
      nombre: 'Programación Web',
      seccion: '002',
      docente: 'ING. JORGE MORALES',
      horarios: [
        { dia: 'L', hora: '16:00 - 17:59' },
        { dia: 'M', hora: '16:00 - 17:59' },
        { dia: 'J', hora: '16:00 - 17:59' }
      ],
      salon: 'Lab. 2'
    },
    {
      id: 10,
      nrc: '50313',
      clave: 'DBA 410',
      nombre: 'Bases de Datos',
      seccion: '001',
      docente: 'MTRO. ARTURO NAVA',
      horarios: [
        { dia: 'A', hora: '18:00 - 19:59' },
        { dia: 'J', hora: '18:00 - 19:59' }
      ],
      salon: 'Lab. 4'
    }
  ];

  constructor(private http: HttpClient) {}

  getMaterias(query: MateriasQuery = {}): Observable<MateriasPage> {
    const normalizedQuery = this.normalizeQuery(query);
    const httpParams = new HttpParams({
      fromObject: {
        search: normalizedQuery.search,
        page: String(normalizedQuery.page),
        page_size: String(normalizedQuery.pageSize)
      }
    });

    return this.http.get<unknown>(this.buildApiUrl(this.materiasApiUrl), { params: httpParams }).pipe(
      map((response) => this.normalizeResponse(response, normalizedQuery)),
      catchError(() => of(this.getLocalPage(normalizedQuery)))
    );
  }

  private buildApiUrl(path: string): string {
    const baseUrl = environment.apiBaseUrl || environment.url_api || '';

    return `${baseUrl.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
  }

  private normalizeQuery(query: MateriasQuery): Required<MateriasQuery> {
    return {
      search: (query.search ?? '').trim(),
      page: Math.max(1, query.page ?? 1),
      pageSize: Math.max(1, query.pageSize ?? 5)
    };
  }

  private normalizeResponse(response: unknown, query: Required<MateriasQuery>): MateriasPage {
    if (Array.isArray(response)) {
      return this.buildPage(response as MateriaItem[], query);
    }

    if (response && typeof response === 'object') {
      const payload = response as Record<string, any>;
      const nestedResults = this.extractResults(payload);

      if (nestedResults) {
        return this.buildPage(nestedResults, {
          search: query.search,
          page: Number(payload['page'] ?? query.page) || query.page,
          pageSize: Number(payload['pageSize'] ?? payload['page_size'] ?? query.pageSize) || query.pageSize
        }, Number(payload['count'] ?? payload['total'] ?? nestedResults.length) || nestedResults.length, false);
      }
    }

    return this.getLocalPage(query);
  }

  private extractResults(payload: Record<string, any>): MateriaItem[] | null {
    const candidates = [payload['results'], payload['data'], payload['items'], payload['materias']];

    for (const candidate of candidates) {
      if (Array.isArray(candidate)) {
        return candidate as MateriaItem[];
      }

      if (candidate && typeof candidate === 'object' && Array.isArray(candidate.results)) {
        return candidate.results as MateriaItem[];
      }
    }

    return null;
  }

  private getLocalPage(query: Required<MateriasQuery>): MateriasPage {
    const filtered = this.filterLocalMaterias(query.search);
    return this.buildPage(filtered, query, filtered.length, true);
  }

  private buildPage(items: MateriaItem[], query: Required<MateriasQuery>, totalOverride?: number, shouldSlice = true): MateriasPage {
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

  private filterLocalMaterias(search: string): MateriaItem[] {
    if (!search) {
      return [...this.materiasCache];
    }

    const normalizedSearch = search.toLowerCase();

    return this.materiasCache.filter((materia) => {
      const haystack = [
        materia.nrc,
        materia.clave,
        materia.nombre,
        materia.seccion,
        materia.docente,
        materia.salon,
        materia.horarios.map((item) => `${item.dia} ${item.hora}`).join(' ')
      ].join(' ').toLowerCase();

      return haystack.includes(normalizedSearch);
    });
  }

}