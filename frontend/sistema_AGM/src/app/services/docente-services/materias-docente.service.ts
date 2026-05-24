import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, map, Observable, of } from 'rxjs';

import { environment } from '../../../environments/environment';

export type MateriaDocenteEstado = 'Activo' | 'Terminado';

export interface MateriaDocenteSesion {
  dia: string;
  hora: string;
}

export interface MateriaDocenteItem {
  id: number;
  nrc: string;
  clave: string;
  materia: string;
  seccion: string;
  estado: MateriaDocenteEstado;
  salon: string;
  sesiones: MateriaDocenteSesion[];
}

@Injectable({
  providedIn: 'root'
})
export class MateriasDocenteService {

  private readonly materiasApiUrl = '/docente/materias/';
  private readonly materiasCache: MateriaDocenteItem[] = [
    {
      id: 1,
      nrc: '50030',
      clave: 'CCOS 260',
      materia: 'Redes de Computadoras',
      seccion: '001',
      estado: 'Activo',
      salon: '1CC04/305',
      sesiones: [
        { dia: 'L', hora: '1000-1059' },
        { dia: 'A', hora: '0900-1059' },
        { dia: 'J', hora: '0900-1059' }
      ]
    },
    {
      id: 2,
      nrc: '48712',
      clave: 'CCOS 270',
      materia: 'Arquitectura de Computadoras',
      seccion: '002',
      estado: 'Activo',
      salon: '1CC04/305',
      sesiones: [
        { dia: 'M', hora: '0800-0959' },
        { dia: 'J', hora: '0800-0959' }
      ]
    },
    {
      id: 3,
      nrc: '52109',
      clave: 'CCOS 312',
      materia: 'Bases de Datos',
      seccion: '003',
      estado: 'Activo',
      salon: '1CC03/118',
      sesiones: [
        { dia: 'L', hora: '1100-1259' },
        { dia: 'M', hora: '1100-1259' }
      ]
    },
    {
      id: 4,
      nrc: '53388',
      clave: 'CCOS 340',
      materia: 'Ingeniería de Software',
      seccion: '004',
      estado: 'Activo',
      salon: '1CC01/402',
      sesiones: [
        { dia: 'V', hora: '1300-1459' }
      ]
    }
  ];

  constructor(private http: HttpClient) {}

  getMaterias(): Observable<MateriaDocenteItem[]> {
    return this.http.get<unknown>(this.buildApiUrl(this.materiasApiUrl)).pipe(
      map((response) => this.normalizeResponse(response)),
      catchError(() => of(this.getLocalMaterias()))
    );
  }

  getMateriaByNrc(nrc: string): Observable<MateriaDocenteItem | null> {
    return this.getMaterias().pipe(
      map((materias) => materias.find((materia) => materia.nrc === nrc) ?? null)
    );
  }

  updateMateriaEstado(nrc: string, estado: MateriaDocenteEstado): Observable<MateriaDocenteItem | null> {
    return this.http.patch<MateriaDocenteItem>(
      this.buildApiUrl(`${this.materiasApiUrl}${nrc}/`),
      { estado }
    ).pipe(
      catchError(() => of(this.updateLocalEstado(nrc, estado)))
    );
  }

  private buildApiUrl(path: string): string {
    const baseUrl = environment.apiBaseUrl || environment.url_api || '';

    return `${baseUrl.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
  }

  private normalizeResponse(response: unknown): MateriaDocenteItem[] {
    if (Array.isArray(response)) {
      return response as MateriaDocenteItem[];
    }

    if (response && typeof response === 'object') {
      const payload = response as Record<string, any>;
      const nestedResults = this.extractResults(payload);

      if (nestedResults) {
        return nestedResults;
      }
    }

    return this.getLocalMaterias();
  }

  private extractResults(payload: Record<string, any>): MateriaDocenteItem[] | null {
    const candidates = [payload['results'], payload['data'], payload['items'], payload['materias']];

    for (const candidate of candidates) {
      if (Array.isArray(candidate)) {
        return candidate as MateriaDocenteItem[];
      }

      if (candidate && typeof candidate === 'object' && Array.isArray(candidate.results)) {
        return candidate.results as MateriaDocenteItem[];
      }
    }

    return null;
  }

  private getLocalMaterias(): MateriaDocenteItem[] {
    return this.materiasCache.map((materia) => ({
      ...materia,
      sesiones: materia.sesiones.map((sesion) => ({ ...sesion }))
    }));
  }

  private updateLocalEstado(nrc: string, estado: MateriaDocenteEstado): MateriaDocenteItem | null {
    const materia = this.materiasCache.find((item) => item.nrc === nrc);

    if (!materia) {
      return null;
    }

    materia.estado = estado;
    return {
      ...materia,
      sesiones: materia.sesiones.map((sesion) => ({ ...sesion }))
    };
  }
}