import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, catchError, forkJoin, map, of, switchMap } from 'rxjs';

import { DocenteApiDto } from '../../models/alumnos-api.model';
import { MateriaApiDto } from '../../models/periodos-api.model';
import { DocentesService } from '../admin-services/docentes.service';
import { PeriodosService } from '../admin-services/periodos.service';
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

export interface MateriasDocenteLoadResult {
  periodoActivoNombre: string | null;
  materias: MateriaDocenteItem[];
  emptyMessage: string;
}

@Injectable({ providedIn: 'root' })
export class MateriasDocenteService {
  private readonly materiasPath = 'materias';

  constructor(
    private http: HttpClient,
    private auth: AuthService,
    private docentes: DocentesService,
    private periodos: PeriodosService,
  ) {}

  getMaterias(): Observable<MateriaDocenteItem[]> {
    return this.loadMateriasDocente().pipe(map((result) => result.materias));
  }

  loadMateriasDocente(): Observable<MateriasDocenteLoadResult> {
    const user = this.auth.getStoredUser();
    if (!user?.id) {
      return of({
        periodoActivoNombre: null,
        materias: [],
        emptyMessage: 'Inicia sesion de nuevo para cargar tus materias.',
      });
    }

    return forkJoin({
      periodoActivo: this.periodos.getPeriodoActivo().pipe(catchError(() => of(null))),
      docente: this.docentes.findDocenteApiByUsuarioId(user.id).pipe(catchError(() => of(null))),
    }).pipe(
      switchMap(({ periodoActivo, docente }) => {
        if (!docente) {
          return of({
            periodoActivoNombre: periodoActivo?.nombre ?? null,
            materias: [],
            emptyMessage:
              'No hay un registro de docente vinculado a tu usuario. Importa tu ficha en Admin > Docentes y espera usuario Activo.',
          });
        }

        if (!periodoActivo) {
          return of({
            periodoActivoNombre: null,
            materias: [],
            emptyMessage:
              'No hay periodo activo. Pide al administrador que active el periodo (por ejemplo Otono).',
          });
        }

        const params = new HttpParams({
          fromObject: {
            periodo_id: String(periodoActivo.id),
            limit: '200',
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

              const materias = list
                .filter((dto) =>
                  this.materiaAsignadaADocente(
                    String(dto.docente_nombre ?? ''),
                    docente,
                    dto.docente_id,
                  ),
                )
                .map((dto) => this.mapMateria(dto));

              const nombreDocente = `${docente.nombre} ${docente.apellido}`.trim();
              let emptyMessage = '';
              if (materias.length === 0) {
                emptyMessage =
                  `No hay materias tuyas en ${periodoActivo.nombre}. ` +
                  `En el PDF de programacion el profesor debe coincidir con "${nombreDocente}" ` +
                  '(mismo nombre y apellidos, aunque en otro orden).';
              }

              return {
                periodoActivoNombre: periodoActivo.nombre,
                materias,
                emptyMessage,
              };
            }),
            catchError(() =>
              of({
                periodoActivoNombre: periodoActivo.nombre,
                materias: [],
                emptyMessage: 'No se pudo consultar las materias del periodo activo (MS-2).',
              }),
            ),
          );
      }),
    );
  }

  getMateriasDocente(): Observable<MateriaDocenteItem[]> {
    return this.getMaterias();
  }

  updateMateriaEstado(nrc: string, estado: MateriaDocenteEstado): Observable<MateriaDocenteItem | null> {
    void nrc;
    void estado;
    return this.getMateriaByNrc(nrc);
  }

  getMateriaByNrc(nrc: string): Observable<MateriaDocenteItem | null> {
    return this.periodos.getPeriodoActivo().pipe(
      switchMap((periodo) => {
        const params: Record<string, string> = { nrc, limit: '10', page: '1' };
        if (periodo) {
          params['periodo_id'] = String(periodo.id);
        }
        const httpParams = new HttpParams({ fromObject: params });
        return this.http.get<unknown>(buildApiUrl(`${this.materiasPath}/`), { params: httpParams });
      }),
      switchMap((response) => {
        const userId = this.auth.getStoredUser()?.id;
        if (!userId) {
          return of(this.pickMateriaFromList(response, null));
        }
        return this.docentes.findDocenteApiByUsuarioId(userId).pipe(
          map((docente) => this.pickMateriaFromList(response, docente)),
          catchError(() => of(this.pickMateriaFromList(response, null))),
        );
      }),
      catchError(() => of(null)),
    );
  }

  resolveMateriaIdByNrc(nrc: string): Observable<number | null> {
    return this.getMateriaByNrc(nrc).pipe(map((m) => (m ? m.id : null)));
  }

  /**
   * El PDF guarda el profesor en docente_nombre; MS-3 guarda nombre + apellido.
   * Coincide si comparten tokens significativos (orden distinto, acentos ignorados).
   */
  private materiaAsignadaADocente(
    docenteNombreMateria: string,
    docente: DocenteApiDto,
    docenteIdMateria?: number | null,
  ): boolean {
    if (
      docenteIdMateria != null &&
      docente.id != null &&
      Number(docenteIdMateria) === Number(docente.id)
    ) {
      return true;
    }

    const enMateria = this.normalizeText(docenteNombreMateria);
    if (!enMateria) {
      return false;
    }

    const tokens = this.normalizeText(`${docente.nombre} ${docente.apellido}`)
      .split(/\s+/)
      .filter((token) => token.length >= 2);

    if (tokens.length === 0) {
      return false;
    }

    const coincidencias = tokens.filter((token) => enMateria.includes(token)).length;
    const minimo = tokens.length <= 2 ? tokens.length : 2;
    return coincidencias >= minimo;
  }

  private normalizeText(value: string): string {
    return value
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .trim();
  }

  private pickMateriaFromList(
    response: unknown,
    docente: DocenteApiDto | null,
  ): MateriaDocenteItem | null {
    const data = unwrapAgmData<{ results?: MateriaApiDto[] }>(response);
    const list = Array.isArray(data?.results)
      ? data.results
      : extractAgmListData<MateriaApiDto>(response);
    const dto = docente
      ? list.find((m) =>
          this.materiaAsignadaADocente(String(m.docente_nombre ?? ''), docente, m.docente_id),
        ) ?? list[0]
      : list[0];
    return dto ? this.mapMateria(dto) : null;
  }

  private mapMateria(dto: MateriaApiDto): MateriaDocenteItem {
    const horario = String(dto.horario ?? '');
    const sesiones = horario ? this.parseHorario(horario) : [];

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

  private parseHorario(horario: string): MateriaDocenteSesion[] {
    const texto = horario.replace(/\s+/g, ' ').trim();
    if (!texto) {
      return [];
    }

    const segmentos = texto.split(/\s*\|\s*|;|\n/).map((s) => s.trim()).filter(Boolean);
    const fuente = segmentos.length > 0 ? segmentos : [texto];

    return fuente.map((segmento) => {
      const partes = segmento.split(/\s+/).filter(Boolean);
      if (partes.length >= 2 && /\d/.test(partes[partes.length - 1])) {
        return {
          dia: partes.slice(0, -1).join(' '),
          hora: this.formatHora(partes[partes.length - 1]),
        };
      }
      return { dia: 'Horario', hora: this.formatHora(segmento) };
    });
  }

  private formatHora(raw: string): string {
    const value = raw.trim();
    const buap = value.match(/^(\d{3,4})\s*-\s*(\d{3,4})$/);
    if (buap) {
      const toClock = (n: string) => {
        const padded = n.padStart(4, '0');
        return `${padded.slice(0, 2)}:${padded.slice(2, 4)}`;
      };
      return `${toClock(buap[1])} – ${toClock(buap[2])}`;
    }

    const standard = value.match(/^(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})$/);
    if (standard) {
      return `${standard[1].padStart(2, '0')}:${standard[2]} – ${standard[3].padStart(2, '0')}:${standard[4]}`;
    }

    return value;
  }
}
