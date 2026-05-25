import { Injectable } from '@angular/core';
import { forkJoin, map, Observable, of, switchMap } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { AlumnoConcentradoDto } from '../../models/calificaciones-api.model';
import { InscripcionMateriaApiDto } from '../../models/alumnos-api.model';
import { AlumnosService } from './alumnos.service';
import { CalificacionesService } from '../docente-services/calificaciones.service';

export interface ParcialMateria {
  titulo: string;
  valor: number | null;
  porcentaje: number;
  activo?: boolean;
}

export interface MateriaAlumno {
  materiaId: number;
  alumnoId: number;
  icono: string;
  color: string;
  nombre: string;
  nrc: string;
  profesor: string;
  promedio: number;
  promedioColor: string;
  expandido: boolean;
  parciales: ParcialMateria[];
  dropped?: boolean;
}

export interface HistorialPeriodo {
  periodo: string;
  materias: number;
  aprobadas: number;
}

@Injectable({ providedIn: 'root' })
export class NotasService {
  private readonly iconos = ['bi-calculator', 'bi-beaker', 'bi-code-slash', 'bi-book'];
  private readonly colores = ['azul', 'naranja', 'morado', 'gris'];

  constructor(
    private alumnos: AlumnosService,
    private calificaciones: CalificacionesService,
  ) {}

  loadMaterias(): Observable<MateriaAlumno[]> {
    return this.alumnos.getMeMaterias(1, 50).pipe(
      switchMap((page) => {
        const inscripciones = page.results.filter((item) => item.activa !== false);
        if (!inscripciones.length) {
          return of([]);
        }

        const requests = inscripciones.map((inscripcion) =>
          this.calificaciones.getConcentrado(Number(inscripcion.materia_id)).pipe(
            map((concentrado) => this.mapMateria(inscripcion, concentrado)),
            catchError(() => of(this.mapMateria(inscripcion, null))),
          ),
        );

        return forkJoin(requests);
      }),
      map((materias) => this.recalcularPromedios(materias)),
    );
  }

  getHistorial(): HistorialPeriodo[] {
    return [];
  }

  recalcularPromedios(materias: MateriaAlumno[]): MateriaAlumno[] {
    return materias.map((materia) => {
      this.recalcularPromedioMateria(materia);
      return materia;
    });
  }

  recalcularPromedioMateria(materia: MateriaAlumno): void {
    const activos = materia.parciales.filter((p) => p.valor !== null && p.valor !== undefined);
    if (!activos.length) {
      materia.promedio = 0;
      materia.promedioColor = 'gris';
      return;
    }

    const totalPeso = activos.reduce((sum, p) => sum + (p.porcentaje || 0), 0) || activos.length;
    const acumulado = activos.reduce((sum, p) => sum + (Number(p.valor) || 0) * (p.porcentaje || 1), 0);
    materia.promedio = Math.round((acumulado / totalPeso) * 10) / 10;
    materia.promedioColor = materia.promedio >= 8 ? 'verde' : materia.promedio >= 6 ? 'naranja' : 'rojo';
  }

  calcularPromedioGeneral(materias: MateriaAlumno[]): number {
    const conNota = materias.filter((m) => !m.dropped && m.promedio > 0);
    if (!conNota.length) {
      return 0;
    }
    const suma = conNota.reduce((acc, m) => acc + m.promedio, 0);
    return Math.round((suma / conNota.length) * 10) / 10;
  }

  marcarBaja(materia: MateriaAlumno): void {
    materia.dropped = true;
    materia.parciales = materia.parciales.map((p) => ({ ...p, activo: false }));
  }

  private mapMateria(
    inscripcion: InscripcionMateriaApiDto,
    concentrado: { alumnos?: AlumnoConcentradoDto[] } | null,
  ): MateriaAlumno {
    const alumno = inscripcion.alumno;
    const matricula = String(alumno?.matricula ?? '');
    const row = concentrado?.alumnos?.find((item) => item.matricula === matricula);

    const parciales: ParcialMateria[] = row
      ? [
          {
            titulo: 'Promedio redondeado',
            valor: Number(row.promedio_redondeado) || null,
            porcentaje: 100,
          },
          {
            titulo: 'Promedio real',
            valor: Number(row.promedio_real) || null,
            porcentaje: 100,
            activo: false,
          },
        ]
      : [{ titulo: 'Sin calificaciones', valor: null, porcentaje: 100, activo: true }];

    const promedio = Number(row?.promedio_redondeado) || 0;

    return {
      materiaId: Number(inscripcion.materia_id),
      alumnoId: Number(alumno?.id ?? 0),
      icono: this.iconos[0],
      color: this.colores[0],
      nombre: String(inscripcion.nombre_materia ?? 'Materia'),
      nrc: String(inscripcion.nrc ?? ''),
      profesor: String(inscripcion.docente_nombre ?? '—'),
      promedio,
      promedioColor: promedio >= 8 ? 'verde' : promedio >= 6 ? 'naranja' : 'rojo',
      expandido: false,
      parciales,
      dropped: !inscripcion.activa,
    };
  }
}
