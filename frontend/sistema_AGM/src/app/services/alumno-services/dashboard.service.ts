import { Injectable } from '@angular/core';
import { forkJoin, map, Observable, of, switchMap } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { ActividadApiDto } from '../../models/calificaciones-api.model';
import { InscripcionMateriaApiDto } from '../../models/alumnos-api.model';
import { AlumnosService } from './alumnos.service';
import { horarioIncluyeDia } from './horario-dias.util';
import { PeriodosService } from '../admin-services/periodos.service';
import { CalificacionesService } from '../docente-services/calificaciones.service';

export interface AlumnoResumen {
  nombre: string;
  matricula: string;
  tipoFormacion?: string;
  periodoActivo?: string;
}

export interface MateriaActual {
  nrc: string;
  materiaId: number;
  nombre: string;
  docente: string;
  seccion: string;
}

export interface MateriaHoy {
  icono: string;
  color: string;
  materia: string;
  aula: string;
  horario: string;
}

export interface EvaluacionItem {
  materia: string;
  fecha: string;
  valor: string;
}

export interface AlumnoDashboardData {
  materiasActuales: MateriaActual[];
  materiasHoy: MateriaHoy[];
  evaluaciones: EvaluacionItem[];
  periodoActivo: string;
}

const DIA_CODIGOS: Record<number, string> = {
  0: 'DOM',
  1: 'LUN',
  2: 'MAR',
  3: 'MIÉ',
  4: 'JUE',
  5: 'VIE',
  6: 'SÁB',
};

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly iconos = ['bi-journal-bookmark', 'bi-cpu', 'bi-bezier2', 'bi-diagram-3'];
  private readonly colores = ['azul', 'naranja', 'morado', 'gris'];

  constructor(
    private alumnos: AlumnosService,
    private periodos: PeriodosService,
    private calificaciones: CalificacionesService,
  ) {}

  loadDashboard(): Observable<AlumnoDashboardData> {
    return forkJoin({
      periodo: this.periodos.getPeriodoActivo().pipe(catchError(() => of(null))),
      inscripciones: this.alumnos.getMeMaterias(1, 100),
    }).pipe(
      switchMap(({ periodo, inscripciones }) => {
        const periodoNombre = periodo?.nombre ?? '—';
        const activas = inscripciones.results.filter((item) => item.activa !== false);
        const base = this.mapInscripciones(activas, periodoNombre);

        if (!activas.length) {
          return of(base);
        }

        const actividades$ = activas.map((inscripcion) =>
          this.calificaciones.getActividades(Number(inscripcion.materia_id)).pipe(
            map((dto) => ({
              nombreMateria: String(inscripcion.nombre_materia ?? 'Materia'),
              actividades: this.flattenActividades(dto.categorias),
            })),
            catchError(() =>
              of({
                nombreMateria: String(inscripcion.nombre_materia ?? 'Materia'),
                actividades: [] as ActividadApiDto[],
              }),
            ),
          ),
        );

        return forkJoin(actividades$).pipe(
          map((grupos) => ({
            ...base,
            evaluaciones: this.mapProximasEvaluaciones(grupos),
          })),
        );
      }),
    );
  }

  getFechaHoyLabel(): string {
    return new Intl.DateTimeFormat('es-MX', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    }).format(new Date());
  }

  private flattenActividades(
    categorias: Array<{
      categoria_nombre: string;
      categoria_porcentaje: string | number;
      actividades: ActividadApiDto[];
    }>,
  ): ActividadApiDto[] {
    const items: ActividadApiDto[] = [];
    for (const categoria of categorias ?? []) {
      for (const actividad of categoria.actividades ?? []) {
        items.push({
          ...actividad,
          categoria_nombre: actividad.categoria_nombre || categoria.categoria_nombre,
          categoria_porcentaje: actividad.categoria_porcentaje ?? categoria.categoria_porcentaje,
        });
      }
    }
    return items;
  }

  private mapProximasEvaluaciones(
    grupos: Array<{ nombreMateria: string; actividades: ActividadApiDto[] }>,
  ): EvaluacionItem[] {
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);

    const items: Array<EvaluacionItem & { sortKey: number }> = [];

    for (const grupo of grupos) {
      for (const actividad of grupo.actividades) {
        if (!actividad.fecha) continue;
        const fecha = new Date(`${actividad.fecha}T12:00:00`);
        if (Number.isNaN(fecha.getTime()) || fecha < hoy) continue;

        items.push({
          materia: grupo.nombreMateria,
          fecha: fecha.toLocaleDateString('es-MX', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
          }),
          valor: `${actividad.categoria_porcentaje}% · ${actividad.nombre}`,
          sortKey: fecha.getTime(),
        });
      }
    }

    return items
      .sort((a, b) => a.sortKey - b.sortKey)
      .slice(0, 8)
      .map(({ materia, fecha, valor }) => ({ materia, fecha, valor }));
  }

  private mapInscripciones(
    inscripciones: InscripcionMateriaApiDto[],
    periodoNombre: string,
  ): AlumnoDashboardData {
    const activas = inscripciones.filter((item) => item.activa !== false);
    const diaHoy = DIA_CODIGOS[new Date().getDay()];

    const materiasActuales: MateriaActual[] = activas.map((item) => {
      const detail = item.materia_detail as Record<string, unknown> | undefined;
      return {
        nrc: String(item.nrc ?? detail?.['nrc'] ?? '—'),
        materiaId: Number(item.materia_id ?? 0),
        nombre: String(item.nombre_materia ?? detail?.['nombre'] ?? 'Materia'),
        docente: String(item.docente_nombre ?? detail?.['docente_nombre'] ?? '—'),
        seccion: String(detail?.['seccion'] ?? detail?.['clave'] ?? item.nrc ?? '—'),
      };
    });

    const materiasHoy: MateriaHoy[] = activas
      .filter((item) => this.inscripcionEsHoy(item, diaHoy))
      .map((item, index) => {
        const detail = item.materia_detail as Record<string, unknown> | undefined;
        const horario = String(item.horario ?? detail?.['horario'] ?? 'Sin horario registrado');
        return {
          icono: this.iconos[index % this.iconos.length],
          color: this.colores[index % this.colores.length],
          materia: String(item.nombre_materia ?? detail?.['nombre'] ?? 'Materia'),
          aula: String(detail?.['salon'] ?? detail?.['aula'] ?? '—'),
          horario,
        };
      });

    return {
      materiasActuales,
      materiasHoy,
      evaluaciones: [],
      periodoActivo: periodoNombre,
    };
  }

  private inscripcionEsHoy(item: InscripcionMateriaApiDto, diaHoy: string): boolean {
    const horario = String(item.horario ?? '');
    return horarioIncluyeDia(horario, diaHoy);
  }
}
