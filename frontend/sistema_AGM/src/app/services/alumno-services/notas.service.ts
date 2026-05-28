import { Injectable } from '@angular/core';
import { forkJoin, map, Observable, of, switchMap } from 'rxjs';
import { catchError } from 'rxjs/operators';

import {
  ActividadesMateriaDto,
  AlumnoConcentradoDto,
  ConcentradoMateriaDto,
} from '../../models/calificaciones-api.model';
import { InscripcionMateriaApiDto } from '../../models/alumnos-api.model';
import { AlumnosService } from './alumnos.service';
import { CalificacionesService } from '../docente-services/calificaciones.service';
import { PeriodosService } from '../admin-services/periodos.service';

export interface ParcialMateria {
  titulo: string;
  valor: number | null;
  porcentaje: number;
  activo?: boolean;
}

/** Calificación explícita de una actividad (la que capturó el docente en MS-4). */
export interface CalificacionActividadAlumno {
  actividadId: number;
  nombre: string;
  categoria: string;
  categoriaPorcentaje: number;
  /** null = el docente aún no registra nota en esa actividad */
  calificacion: number | null;
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
  promedioReal: number | null;
  promedioRedondeado: number | null;
  expandido: boolean;
  /** Actividades del plan con la nota recibida (o pendiente). */
  actividades: CalificacionActividadAlumno[];
  parciales: ParcialMateria[];
  dropped?: boolean;
}

export interface HistorialPeriodo {
  periodo: string;
  materias: number;
  aprobadas: number;
}

export interface NotasCargaResult {
  materias: MateriaAlumno[];
  historial: HistorialPeriodo[];
  progresoPeriodo: number;
}

@Injectable({ providedIn: 'root' })
export class NotasService {
  private readonly iconos = ['bi-calculator', 'bi-beaker', 'bi-code-slash', 'bi-book'];
  private readonly colores = ['azul', 'naranja', 'morado', 'gris'];

  constructor(
    private alumnos: AlumnosService,
    private calificaciones: CalificacionesService,
    private periodos: PeriodosService,
  ) {}

  loadNotas(): Observable<NotasCargaResult> {
    return forkJoin({
      periodo: this.periodos.getPeriodoActivo().pipe(catchError(() => of(null))),
      inscripciones: this.alumnos.getMeMaterias(1, 50),
    }).pipe(
      switchMap(({ periodo, inscripciones }) => {
        const activas = inscripciones.results.filter((item) => item.activa !== false);
        const periodoNombre = periodo?.nombre ?? 'Periodo actual';

        if (!activas.length) {
          return of({
            materias: [],
            historial: [{ periodo: periodoNombre, materias: 0, aprobadas: 0 }],
            progresoPeriodo: 0,
          });
        }

        const requests = activas.map((inscripcion, index) => {
          const materiaId = Number(inscripcion.materia_id);
          return forkJoin({
            concentrado: this.calificaciones.getConcentrado(materiaId).pipe(catchError(() => of(null))),
            actividades: this.calificaciones.getActividades(materiaId).pipe(catchError(() => of(null))),
          }).pipe(
            map(({ concentrado, actividades }) =>
              this.mapMateria(inscripcion, concentrado, actividades, index),
            ),
          );
        });

        return forkJoin(requests).pipe(
          map((materias) => {
            const normalizadas = this.recalcularPromedios(materias);
            return {
              materias: normalizadas,
              historial: this.buildHistorial(periodoNombre, normalizadas),
              progresoPeriodo: this.calcularProgresoPeriodo(normalizadas),
            };
          }),
        );
      }),
    );
  }

  /** @deprecated Usar loadNotas() */
  loadMaterias(): Observable<MateriaAlumno[]> {
    return this.loadNotas().pipe(map((result) => result.materias));
  }

  recalcularPromedios(materias: MateriaAlumno[]): MateriaAlumno[] {
    return materias.map((materia) => {
      this.recalcularPromedioMateria(materia);
      return materia;
    });
  }

  recalcularPromedioMateria(materia: MateriaAlumno): void {
    const rowPromedio = materia.parciales.find((p) => p.titulo === 'Promedio redondeado');
    if (rowPromedio?.valor != null) {
      materia.promedio = Number(rowPromedio.valor) || 0;
      materia.promedioColor =
        materia.promedio >= 8 ? 'verde' : materia.promedio >= 6 ? 'naranja' : 'rojo';
      return;
    }

    const activos = materia.parciales.filter(
      (p) =>
        p.valor !== null &&
        p.valor !== undefined &&
        !p.titulo.toLowerCase().includes('promedio'),
    );
    if (!activos.length) {
      materia.promedio = 0;
      materia.promedioColor = 'gris';
      return;
    }

    const totalPeso = activos.reduce((sum, p) => sum + (p.porcentaje || 0), 0) || activos.length;
    const acumulado = activos.reduce(
      (sum, p) => sum + (Number(p.valor) || 0) * (p.porcentaje || 1),
      0,
    );
    materia.promedio = Math.round((acumulado / totalPeso) * 10) / 10;
    materia.promedioColor =
      materia.promedio >= 8 ? 'verde' : materia.promedio >= 6 ? 'naranja' : 'rojo';
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

  private buildHistorial(periodoNombre: string, materias: MateriaAlumno[]): HistorialPeriodo[] {
    const activas = materias.filter((m) => !m.dropped);
    const aprobadas = activas.filter((m) => m.promedio >= 6).length;
    return [
      {
        periodo: periodoNombre,
        materias: activas.length,
        aprobadas,
      },
    ];
  }

  private calcularProgresoPeriodo(materias: MateriaAlumno[]): number {
    const activas = materias.filter((m) => !m.dropped);
    if (!activas.length) {
      return 0;
    }
    const conCalificacion = activas.filter((m) =>
      m.actividades.some((a) => a.calificacion !== null && a.calificacion !== undefined),
    ).length;
    return Math.round((conCalificacion / activas.length) * 100);
  }

  private mapMateria(
    inscripcion: InscripcionMateriaApiDto,
    concentrado: ConcentradoMateriaDto | null,
    actividadesDto: ActividadesMateriaDto | null,
    index: number,
  ): MateriaAlumno {
    const alumno = inscripcion.alumno;
    const matricula = String(alumno?.matricula ?? '');
    const row = concentrado?.alumnos?.find((item) => item.matricula === matricula);
    const actividades = this.mapActividadesConNotas(row, concentrado, actividadesDto);
    const parciales = this.mapParcialesResumen(row);
    const promedioRedondeado =
      row?.promedio_redondeado != null ? Number(row.promedio_redondeado) : null;
    const promedioReal = row?.promedio_real != null ? Number(row.promedio_real) : null;
    const promedio = promedioRedondeado ?? 0;

    return {
      materiaId: Number(inscripcion.materia_id),
      alumnoId: Number(alumno?.id ?? 0),
      icono: this.iconos[index % this.iconos.length],
      color: this.colores[index % this.colores.length],
      nombre: String(inscripcion.nombre_materia ?? 'Materia'),
      nrc: String(inscripcion.nrc ?? ''),
      profesor: String(inscripcion.docente_nombre ?? '—'),
      promedio,
      promedioColor: promedio >= 8 ? 'verde' : promedio >= 6 ? 'naranja' : 'rojo',
      promedioReal,
      promedioRedondeado,
      expandido: false,
      actividades,
      parciales,
      dropped: !inscripcion.activa,
    };
  }

  private mapActividadesConNotas(
    row: AlumnoConcentradoDto | undefined,
    concentrado: ConcentradoMateriaDto | null,
    actividadesDto: ActividadesMateriaDto | null,
  ): CalificacionActividadAlumno[] {
    const notasPorActividad = new Map<number, number>();
    for (const item of row?.calificaciones ?? []) {
      const id = Number(item.actividad_id);
      if (!Number.isNaN(id)) {
        notasPorActividad.set(id, Number(item.calificacion));
      }
    }

    const lista: CalificacionActividadAlumno[] = [];
    const categorias = concentrado?.categorias?.length
      ? concentrado.categorias
      : (actividadesDto?.categorias ?? []).map((c) => ({
          nombre: c.categoria_nombre,
          porcentaje: c.categoria_porcentaje,
          actividades: (c.actividades ?? []).map((a) => ({ id: a.id, nombre: a.nombre })),
        }));

    for (const categoria of categorias) {
      const catNombre = String(categoria.nombre ?? 'Rubro');
      const catPct = Number(categoria.porcentaje) || 0;
      for (const actividad of categoria.actividades ?? []) {
        const actividadId = Number(actividad.id);
        lista.push({
          actividadId,
          nombre: String(actividad.nombre ?? `Actividad ${actividadId}`),
          categoria: catNombre,
          categoriaPorcentaje: catPct,
          calificacion: notasPorActividad.has(actividadId)
            ? notasPorActividad.get(actividadId)!
            : null,
        });
      }
    }

    for (const item of row?.calificaciones ?? []) {
      const actividadId = Number(item.actividad_id);
      if (lista.some((entry) => entry.actividadId === actividadId)) {
        continue;
      }
      lista.push({
        actividadId,
        nombre: String(item.actividad_nombre ?? `Actividad ${actividadId}`),
        categoria: String(item.categoria ?? '—'),
        categoriaPorcentaje: 0,
        calificacion: Number(item.calificacion),
      });
    }

    return lista;
  }

  private mapParcialesResumen(row: AlumnoConcentradoDto | undefined): ParcialMateria[] {
    if (!row) {
      return [];
    }

    const parciales: ParcialMateria[] = [];

    if (row.promedio_redondeado != null) {
      parciales.push({
        titulo: 'Promedio redondeado',
        valor: Number(row.promedio_redondeado),
        porcentaje: 100,
        activo: true,
      });
    }

    if (row.promedio_real != null) {
      parciales.push({
        titulo: 'Promedio ponderado real',
        valor: Number(row.promedio_real),
        porcentaje: 100,
        activo: false,
      });
    }

    return parciales;
  }
}
