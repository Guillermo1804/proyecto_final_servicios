import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, map, of, switchMap } from 'rxjs';

import { MateriaApiDto } from '../../models/periodos-api.model';
import { DocentesService } from '../admin-services/docentes.service';
import { AuthService } from '../auth.service';
import {
  buildApiUrl,
  extractAgmListData,
  unwrapAgmData,
} from '../tools/agm-api.helpers';

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

@Injectable({ providedIn: 'root' })
export class MateriasDocenteService {
  private readonly materiasPath = 'materias';

  constructor(
    private http: HttpClient,
    private auth: AuthService,
    private docentes: DocentesService,
  ) {}

  getMaterias(): Observable<MateriaDocenteItem[]> {
    return this.getMateriasDocente();
  }

  getMateriasDocente(): Observable<MateriaDocenteItem[]> {
    const user = this.auth.getStoredUser();
    if (!user?.id) {
      return of([]);
    }

    return this.docentes.findDocenteByUsuarioId(user.id).pipe(
      switchMap((docente) => {
        if (!docente) {
          return of([]);
        }
        const params = new HttpParams({
          fromObject: {
            docente_nombre: docente.nombre,
            limit: '100',
            page: '1',
          },
        });

        return this.http
          .get<unknown>(buildApiUrl(`${this.materiasPath}/`), { params })
          .pipe(
            map((response) => {
              const data = unwrapAgmData<{ results?: MateriaApiDto[] }>(response);
              const list = Array.isArray(data?.results)
                ? data.results
                : extractAgmListData<MateriaApiDto>(response);
              return list.map((dto) => this.mapMateria(dto));
            }),
          );
      }),
    );
  }

  updateMateriaEstado(nrc: string, estado: MateriaDocenteEstado): Observable<MateriaDocenteItem | null> {
    void nrc;
    void estado;
    return this.getMateriaByNrc(nrc);
  }

  getMateriaByNrc(nrc: string): Observable<MateriaDocenteItem | null> {
    const params = new HttpParams({ fromObject: { nrc, limit: '1', page: '1' } });
    return this.http.get<unknown>(buildApiUrl(`${this.materiasPath}/`), { params }).pipe(
      map((response) => {
        const data = unwrapAgmData<{ results?: MateriaApiDto[] }>(response);
        const list = Array.isArray(data?.results)
          ? data.results
          : extractAgmListData<MateriaApiDto>(response);
        const dto = list[0];
        return dto ? this.mapMateria(dto) : null;
      }),
    );
  }

  resolveMateriaIdByNrc(nrc: string): Observable<number | null> {
    return this.getMateriaByNrc(nrc).pipe(map((m) => (m ? m.id : null)));
  }

  private mapMateria(dto: MateriaApiDto): MateriaDocenteItem {
    const horario = String(dto.horario ?? '');
    const sesiones = horario
      ? [{ dia: '—', hora: horario }]
      : [];

    return {
      id: Number(dto.id),
      nrc: String(dto.nrc ?? ''),
      clave: String(dto.clave ?? ''),
      materia: String(dto.nombre ?? ''),
      seccion: String(dto.seccion ?? ''),
      estado: 'Activo',
      salon: '—',
      sesiones,
    };
  }
}
