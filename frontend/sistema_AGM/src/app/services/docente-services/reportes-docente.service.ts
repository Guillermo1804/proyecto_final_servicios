import { Injectable } from '@angular/core';
import { forkJoin, map, Observable, of, switchMap } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { ConcentradoMateriaDto } from '../../models/calificaciones-api.model';
import { MateriaDocenteItem } from './materias-docente.service';
import { AlumnosService } from '../alumno-services/alumnos.service';
import { PeriodosService } from '../admin-services/periodos.service';
import { CalificacionesService } from './calificaciones.service';
import { MateriasDocenteService } from './materias-docente.service';

export interface ReporteExportacionItem {
  documento: string;
  materia: string;
  fecha: string;
}

export interface ReporteAcademicoMateriaItem {
  nombre: string;
  grupo: string;
  alumnos: number;
  promedio: number;
  aprobacion: number;
}

export interface ReporteAcademicoPeriodoItem {
  periodo: string;
  activo: boolean;
  resumen: string;
  materias: ReporteAcademicoMateriaItem[];
}

export interface ReporteComparativaItem {
  nombre: string;
  repeticiones: number;
  promedioActual: number;
  promedioAnterior: number;
  variacionPromedio: string;
  aprobacionActual: number;
  aprobacionAnterior: number;
  variacionAprobacion: string;
  periodos: string[];
}

export interface ReportePeriodoEscolarItem {
  nombre: string;
  activo: boolean;
}

export interface ReporteMateriaOpcionItem {
  id: number;
  label: string;
}

export interface ReportesDocenteResumen {
  promedioGeneral: number;
  indiceAprobacion: number;
  alumnosAprobados: number;
  alumnosEnRiesgo: number;
  materiasActivas: number;
}

export interface ReportesDocenteData {
  periodosEscolares: ReportePeriodoEscolarItem[];
  historial: ReporteExportacionItem[];
  historialAcademico: ReporteAcademicoPeriodoItem[];
  materiasComparadas: ReporteComparativaItem[];
  materiasOpciones: ReporteMateriaOpcionItem[];
  resumen: ReportesDocenteResumen;
  insightObservacion: string;
  insightAccion: string;
}

@Injectable({ providedIn: 'root' })
export class ReportesDocenteService {
  constructor(
    private periodos: PeriodosService,
    private materiasDocente: MateriasDocenteService,
    private calificaciones: CalificacionesService,
    private alumnos: AlumnosService,
  ) {}

  loadReportes(): Observable<ReportesDocenteData> {
    return forkJoin({
      periodosPage: this.periodos.getPeriodos({ page: 1, pageSize: 50 }),
      materiasLoad: this.materiasDocente.loadMateriasDocente(),
    }).pipe(
      switchMap(({ periodosPage, materiasLoad }) => {
        const periodosEscolares: ReportePeriodoEscolarItem[] = periodosPage.results.map((p) => ({
          nombre: p.nombre,
          activo: p.activo,
        }));

        const materias = materiasLoad.materias;
        if (!materias.length) {
          return of(this.buildEmpty(periodosEscolares, materiasLoad.periodoActivoNombre));
        }

        const stats$ = materias.map((materia) =>
          forkJoin({
            concentrado: this.calificaciones.getConcentrado(materia.id).pipe(
              catchError(() => of(null as ConcentradoMateriaDto | null)),
            ),
            inscripciones: this.alumnos
              .getAlumnosPorMateria(materia.id, 1, 1)
              .pipe(catchError(() => of({ count: 0, results: [] }))),
          }).pipe(
            map(({ concentrado, inscripciones }) =>
              this.mapMateriaStats(materia, concentrado, Number(inscripciones.count ?? 0)),
            ),
          ),
        );

        return forkJoin(stats$).pipe(
          map((materiasStats) => {
            const periodoActivoNombre =
              materiasLoad.periodoActivoNombre ||
              periodosPage.results.find((p) => p.activo)?.nombre ||
              'Periodo activo';

            const historialAcademico: ReporteAcademicoPeriodoItem[] = [
              {
                periodo: periodoActivoNombre,
                activo: true,
                resumen: this.buildResumenPeriodo(materiasStats),
                materias: materiasStats,
              },
              ...periodosPage.results
                .filter((p) => !p.activo)
                .map((p) => ({
                  periodo: p.nombre,
                  activo: false,
                  resumen: 'Sin materias cargadas para este periodo en la vista del docente.',
                  materias: [] as ReporteAcademicoMateriaItem[],
                })),
            ];

            const materiasComparadas = this.buildComparativas(historialAcademico);
            const resumen = this.buildResumen(materiasStats);
            const insights = this.buildInsights(materiasStats);

            return {
              periodosEscolares,
              historial: [],
              historialAcademico,
              materiasComparadas,
              materiasOpciones: materias.map((m) => ({
                id: m.id,
                label: `${m.materia} · NRC ${m.nrc}`,
              })),
              resumen,
              insightObservacion: insights.observacion,
              insightAccion: insights.accion,
            };
          }),
        );
      }),
      catchError(() =>
        of({
          periodosEscolares: [],
          historial: [],
          historialAcademico: [],
          materiasComparadas: [],
          materiasOpciones: [],
          resumen: {
            promedioGeneral: 0,
            indiceAprobacion: 0,
            alumnosAprobados: 0,
            alumnosEnRiesgo: 0,
            materiasActivas: 0,
          },
          insightObservacion: 'No se pudieron cargar los datos del reporte.',
          insightAccion: 'Verifica que MS-2, MS-3 y MS-4 estén activos.',
        }),
      ),
    );
  }

  private buildEmpty(
    periodosEscolares: ReportePeriodoEscolarItem[],
    periodoNombre: string | null,
  ): ReportesDocenteData {
    return {
      periodosEscolares,
      historial: [],
      historialAcademico: periodoNombre
        ? [
            {
              periodo: periodoNombre,
              activo: true,
              resumen: 'No hay materias asignadas en el periodo activo.',
              materias: [],
            },
          ]
        : [],
      materiasComparadas: [],
      materiasOpciones: [],
      resumen: {
        promedioGeneral: 0,
        indiceAprobacion: 0,
        alumnosAprobados: 0,
        alumnosEnRiesgo: 0,
        materiasActivas: 0,
      },
      insightObservacion: 'Sin materias para analizar.',
      insightAccion: 'Importa tu programacion de materias o revisa el periodo activo.',
    };
  }

  private mapMateriaStats(
    materia: MateriaDocenteItem,
    concentrado: ConcentradoMateriaDto | null,
    alumnosInscritos: number,
  ): ReporteAcademicoMateriaItem {
    const rows = concentrado?.alumnos ?? [];
    const conNota = rows.filter((r) => Number(r.promedio_redondeado) > 0);
    const promedio =
      conNota.length > 0
        ? Math.round(
            (conNota.reduce((s, r) => s + Number(r.promedio_redondeado), 0) / conNota.length) * 10,
          ) / 10
        : 0;
    const aprobados = rows.filter((r) => Number(r.promedio_redondeado) >= 6).length;
    const total = rows.length || alumnosInscritos;
    const aprobacion = total > 0 ? Math.round((aprobados / total) * 100) : 0;

    return {
      nombre: materia.materia,
      grupo: materia.seccion || materia.clave || materia.nrc,
      alumnos: total || alumnosInscritos,
      promedio,
      aprobacion,
    };
  }

  private buildResumenPeriodo(materias: ReporteAcademicoMateriaItem[]): string {
    if (!materias.length) {
      return 'Sin materias en el periodo activo.';
    }
    const promedio =
      Math.round((materias.reduce((s, m) => s + m.promedio, 0) / materias.length) * 10) / 10;
    return `${materias.length} materia(s) con promedio grupal ${promedio}.`;
  }

  private buildResumen(materias: ReporteAcademicoMateriaItem[]): ReportesDocenteResumen {
    const materiasActivas = materias.length;
    const promedioGeneral =
      materiasActivas > 0
        ? Math.round((materias.reduce((s, m) => s + m.promedio, 0) / materiasActivas) * 100) / 100
        : 0;
    const totalAlumnos = materias.reduce((s, m) => s + m.alumnos, 0);
    const aprobacionPonderada =
      totalAlumnos > 0
        ? materias.reduce((s, m) => s + (m.aprobacion / 100) * m.alumnos, 0) / totalAlumnos
        : 0;
    const indiceAprobacion = Math.round(aprobacionPonderada * 1000) / 10;
    const alumnosAprobados = materias.reduce(
      (s, m) => s + Math.round((m.aprobacion / 100) * m.alumnos),
      0,
    );
    const alumnosEnRiesgo = materias.reduce(
      (s, m) => s + Math.max(0, m.alumnos - Math.round((m.aprobacion / 100) * m.alumnos)),
      0,
    );

    return {
      promedioGeneral,
      indiceAprobacion,
      alumnosAprobados,
      alumnosEnRiesgo,
      materiasActivas,
    };
  }

  private buildComparativas(
    historial: ReporteAcademicoPeriodoItem[],
  ): ReporteComparativaItem[] {
    const porNombre = new Map<string, Array<{ periodo: string; stats: ReporteAcademicoMateriaItem }>>();

    for (const periodo of historial) {
      for (const materia of periodo.materias) {
        const key = materia.nombre.trim().toLowerCase();
        if (!key) continue;
        const list = porNombre.get(key) ?? [];
        list.push({ periodo: periodo.periodo, stats: materia });
        porNombre.set(key, list);
      }
    }

    const comparativas: ReporteComparativaItem[] = [];
    for (const [, entries] of porNombre) {
      if (entries.length < 2) continue;
      const ordenados = [...entries].sort((a, b) => a.periodo.localeCompare(b.periodo));
      const anterior = ordenados[ordenados.length - 2].stats;
      const actual = ordenados[ordenados.length - 1].stats;
      const variacionPromedio = actual.promedio - anterior.promedio;
      const variacionAprobacion = actual.aprobacion - anterior.aprobacion;

      comparativas.push({
        nombre: actual.nombre,
        repeticiones: entries.length,
        promedioActual: actual.promedio,
        promedioAnterior: anterior.promedio,
        variacionPromedio: this.formatVariacion(variacionPromedio),
        aprobacionActual: actual.aprobacion,
        aprobacionAnterior: anterior.aprobacion,
        variacionAprobacion: this.formatVariacion(variacionAprobacion, true),
        periodos: ordenados.map((e) => e.periodo),
      });
    }

    return comparativas;
  }

  private buildInsights(materias: ReporteAcademicoMateriaItem[]): {
    observacion: string;
    accion: string;
  } {
    if (!materias.length) {
      return {
        observacion: 'Sin datos de concentrado para el periodo activo.',
        accion: 'Captura calificaciones en cada materia para generar estadísticas.',
      };
    }

    const mejorAprobacion = [...materias].sort((a, b) => b.aprobacion - a.aprobacion)[0];
    const menorPromedio = [...materias].sort((a, b) => a.promedio - b.promedio)[0];

    return {
      observacion: `${mejorAprobacion.nombre} tiene el mayor índice de aprobación (${mejorAprobacion.aprobacion}%) con promedio ${mejorAprobacion.promedio}.`,
      accion:
        menorPromedio.promedio < 7
          ? `Revisa criterios de evaluación en ${menorPromedio.nombre} (promedio ${menorPromedio.promedio}).`
          : 'El desempeño grupal se mantiene dentro de rangos esperados.',
    };
  }

  private formatVariacion(valor: number, puntos = false): string {
    const signo = valor > 0 ? '+' : '';
    if (puntos) {
      return `${signo}${Math.round(valor)}`;
    }
    return `${signo}${Math.round(valor * 10) / 10}`;
  }
}
