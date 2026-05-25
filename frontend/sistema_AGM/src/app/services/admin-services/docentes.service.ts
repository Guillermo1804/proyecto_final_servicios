import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, map, Observable, of } from 'rxjs';

import { environment } from '../../../environments/environment';

export type DocenteEstado = 'Activo' | 'Inactivo';

export interface DocenteItem {
  id: number;
  nombre: string;
  correo: string;
  ubicacion: string;
  estado: DocenteEstado;
}

export interface DocentesQuery {
  search?: string;
  page?: number;
  pageSize?: number;
}

export interface DocentesPage {
  results: DocenteItem[];
  count: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

@Injectable({
  providedIn: 'root'
})
export class DocentesService {

  private readonly docentesApiUrl = '/docentes/';
  private readonly docentesCache: DocenteItem[] = [
    { id: 1, nombre: 'Dr. Alejandro Vargas', correo: 'alejandro.vargas@agm.edu', ubicacion: 'Ciencias Exactas', estado: 'Activo' },
    { id: 2, nombre: 'Dra. Beatriz Mendoza', correo: 'beatriz.mendoza@agm.edu', ubicacion: 'Ingeniería', estado: 'Inactivo' },
    { id: 3, nombre: 'Mgter. Carlos Ruiz', correo: 'carlos.ruiz@agm.edu', ubicacion: 'Artes y Humanidades', estado: 'Activo' },
    { id: 4, nombre: 'Dra. Diana Soto', correo: 'diana.soto@agm.edu', ubicacion: 'Ciencias de la Salud', estado: 'Inactivo' },
    { id: 5, nombre: 'Mtro. Enrique León', correo: 'enrique.leon@agm.edu', ubicacion: 'Arquitectura', estado: 'Activo' },
    { id: 6, nombre: 'Dra. Fernanda Ortega', correo: 'fernanda.ortega@agm.edu', ubicacion: 'Administración', estado: 'Activo' },
    { id: 7, nombre: 'Ing. Gabriel Pérez', correo: 'gabriel.perez@agm.edu', ubicacion: 'Sistemas', estado: 'Inactivo' },
    { id: 8, nombre: 'Dra. Helena Cruz', correo: 'helena.cruz@agm.edu', ubicacion: 'Matemáticas', estado: 'Activo' },
    { id: 9, nombre: 'Mtro. Ignacio Flores', correo: 'ignacio.flores@agm.edu', ubicacion: 'Biología', estado: 'Activo' },
    { id: 10, nombre: 'Dra. Jimena Ramos', correo: 'jimena.ramos@agm.edu', ubicacion: 'Derecho', estado: 'Inactivo' }
  ];

  constructor(private http: HttpClient) {}

  getDocentes(query: DocentesQuery = {}): Observable<DocentesPage> {
    const normalizedQuery = this.normalizeQuery(query);
    const httpParams = new HttpParams({
      fromObject: {
        search: normalizedQuery.search,
        page: String(normalizedQuery.page),
        page_size: String(normalizedQuery.pageSize)
      }
    });

    return this.http.get<unknown>(this.buildApiUrl(this.docentesApiUrl), { params: httpParams }).pipe(
      map((response) => this.normalizeResponse(response, normalizedQuery)),
      catchError(() => of(this.getLocalPage(normalizedQuery)))
    );
  }

  updateDocenteEstado(docenteId: number, estado: DocenteEstado): Observable<DocenteItem | null> {
    return this.http.patch<DocenteItem>(
      this.buildApiUrl(`${this.docentesApiUrl}${docenteId}/`),
      { estado }
    ).pipe(
      catchError(() => of(this.updateLocalEstado(docenteId, estado)))
    );
  }

  deleteDocente(docenteId: number): Observable<boolean> {
    return this.http.delete<void>(this.buildApiUrl(`${this.docentesApiUrl}${docenteId}/`)).pipe(
      map(() => true),
      catchError(() => of(this.deleteLocalDocente(docenteId)))
    );
  }

  private buildApiUrl(path: string): string {
    const baseUrl = environment.apiBaseUrl || environment.url_api || '';

    return `${baseUrl.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
  }

  private normalizeQuery(query: DocentesQuery): Required<DocentesQuery> {
    return {
      search: (query.search ?? '').trim(),
      page: Math.max(1, query.page ?? 1),
      pageSize: Math.max(1, query.pageSize ?? 5)
    };
  }

  private normalizeResponse(response: unknown, query: Required<DocentesQuery>): DocentesPage {
    if (Array.isArray(response)) {
      return this.buildPage(response as DocenteItem[], query);
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

  private extractResults(payload: Record<string, any>): DocenteItem[] | null {
    const candidates = [payload['results'], payload['data'], payload['items'], payload['docentes']];

    for (const candidate of candidates) {
      if (Array.isArray(candidate)) {
        return candidate as DocenteItem[];
      }

      if (candidate && typeof candidate === 'object' && Array.isArray(candidate.results)) {
        return candidate.results as DocenteItem[];
      }
    }

    return null;
  }

  private getLocalPage(query: Required<DocentesQuery>): DocentesPage {
    const filtered = this.filterLocalDocentes(query.search);
    return this.buildPage(filtered, query, filtered.length, true);
  }

  private buildPage(items: DocenteItem[], query: Required<DocentesQuery>, totalOverride?: number, shouldSlice = true): DocentesPage {
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

  private filterLocalDocentes(search: string): DocenteItem[] {
    if (!search) {
      return [...this.docentesCache];
    }

    const normalizedSearch = search.toLowerCase();

    return this.docentesCache.filter((docente) => {
      const haystack = [docente.nombre, docente.correo, docente.ubicacion, docente.estado].join(' ').toLowerCase();
      return haystack.includes(normalizedSearch);
    });
  }

  private updateLocalEstado(docenteId: number, estado: DocenteEstado): DocenteItem | null {
    const docente = this.docentesCache.find((item) => item.id === docenteId);

    if (!docente) {
      return null;
    }

    docente.estado = estado;
    return { ...docente };
  }

  private deleteLocalDocente(docenteId: number): boolean {
    const index = this.docentesCache.findIndex((item) => item.id === docenteId);

    if (index === -1) {
      return false;
    }

    this.docentesCache.splice(index, 1);
    return true;
  }
}