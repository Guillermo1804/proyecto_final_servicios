import { Injectable } from '@angular/core';
import { forkJoin, map, Observable, of, switchMap } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { ConcentradoMateriaDto } from '../../models/calificaciones-api.model';
import {
  ComparativaMateriaApiDto,
  EstadisticasDocenteApiDto,
  ReporteDescargaFormato,
  ReporteDescargaTipo,
  StatsPeriodoApiDto,
} from '../../models/reportes-api.model';
import { AuthService } from '../auth.service';
import { ReportesService } from '../reportes.service';
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
  materiaId?: number;
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
  fuente: 'ms7' | 'fallback' | 'empty';
}

const HISTORIAL_EXPORT_KEY = 'agm_reportes_export_historial';
const HISTORIAL_MAX = 20;

@Injectable({ providedIn: 'root' })
export class ReportesDocenteService {
  constructor(
    private readonly auth: AuthService,
    private readonly reportes: ReportesService,
    private readonly periodos: PeriodosService,
    private readonly materiasDocente: MateriasDocenteService,
    private readonly calificaciones: CalificacionesService,
    private readonly alumnos: AlumnosService,
  ) {}

  loadReportes(): Observable<ReportesDocenteData> {
    const userId = this.auth.getStoredUser()?.id;
    if (!userId) {
      return of(this.buildSinSesion());
    }

    return forkJoin({
      periodosPage: this.periodos.getPeriodos({ page: 1, pageSize: 50 }).pipe(
        catchError(() => of({ results: [], count: 0, page: 1, pageSize: 50, totalPages: 1 })),
      ),
      estadisticas: this.reportes.getEstadisticasDocente(userId).pipe(catchError(() => of(null))),
      materiasLoad: this.materiasDocente.loadMateriasDocente().pipe(
        catchError(() =>
          of({ materias: [] as MateriaDocenteItem[], periodoActivoNombre: null as string | null }),
        ),
      ),
    }).pipe(
      switchMap(({ periodosPage, estadisticas, materiasLoad }) => {
        const periodosEscolares: ReportePeriodoEscolarItem[] = periodosPage.results.map((p) => ({
          nombre: p.nombre,
          activo: p.activo,
        }));

        const historial = this.getHistorialExportaciones();
        const labelByMateriaId = new Map(
          materiasLoad.materias.map((m) => [m.id, `${m.materia} · NRC ${m.nrc}`]),
        );

        if (estadisticas?.periodos?.length) {
          return of(
            this.mapFromMs7(
              estadisticas,
              periodosEscolares,
              materiasLoad.materias,
              labelByMateriaId,
              historial,
            ),
          );
        }

        return this.loadFallbackAsync(periodosEscolares, materiasLoad, historial);
      }),
      catchError(() => of(this.buildErrorLoad())),
    );
  }

  exportarReporte(
    tipo: ReporteDescargaTipo,
    materiaId: number,
    formato: ReporteDescargaFormato,
  ): Observable<Blob> {
    return this.reportes.descargarReporte(tipo, materiaId, formato);
  }

  registrarExportacion(item: ReporteExportacionItem): void {
    const list = [item, ...this.getHistorialExportaciones()].slice(0, HISTORIAL_MAX);
    sessionStorage.setItem(HISTORIAL_EXPORT_KEY, JSON.stringify(list));
  }

  getHistorialExportaciones(): ReporteExportacionItem[] {
    try {
      const raw = sessionStorage.getItem(HISTORIAL_EXPORT_KEY);
      if (!raw) {
        return [];
      }
      const parsed = JSON.parse(raw) as ReporteExportacionItem[];
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  private mapFromMs7(
    estadisticas: EstadisticasDocenteApiDto,
    periodosEscolares: ReportePeriodoEscolarItem[],
    materiasActivas: MateriaDocenteItem[],
    labelByMateriaId: Map<number, string>,
    historial: ReporteExportacionItem[],
  ): ReportesDocenteData {
    const historialAcademico = this.buildHistorialFromStats(
      estadisticas.periodos,
      periodosEscolares,
      labelByMateriaId,
    );
    const materiasComparadas = this.mapComparativaMs7(estadisticas.comparativa);
    const activo = historialAcademico.find((p) => p.activo);
    const materiasResumen = activo?.materias ?? [];
    const resumen = this.buildResumen(materiasResumen);
    const insights = this.buildInsights(materiasResumen);

    const activoNombre = periodosEscolares.find((p) => p.activo)?.nombre ?? null;
    const idsActivos = new Set(
      estadisticas.periodos
        .filter((row) => !activoNombre || row.periodo_nombre === activoNombre)
        .map((row) => row.materia_id),
    );

    const materiasOpciones: ReporteMateriaOpcionItem[] = [];
    if (materiasActivas.length) {
      for (const m of materiasActivas) {
        if (!activoNombre || !idsActivos.size || idsActivos.has(m.id)) {
          materiasOpciones.push({
            id: m.id,
            label: labelByMateriaId.get(m.id) ?? `${m.materia} · NRC ${m.nrc}`,
          });
        }
      }
    } else {
      for (const row of estadisticas.periodos) {
        if (!activoNombre || row.periodo_nombre === activoNombre) {
          materiasOpciones.push({
            id: row.materia_id,
            label:
              labelByMateriaId.get(row.materia_id) ??
              `${row.materia_nombre} · ID ${row.materia_id}`,
          });
        }
      }
    }

    const opcionesUnicas = new Map<number, ReporteMateriaOpcionItem>();
    for (const op of materiasOpciones) {
      opcionesUnicas.set(op.id, op);
    }

    return {
      periodosEscolares,
      historial,
      historialAcademico,
      materiasComparadas,
      materiasOpciones: [...opcionesUnicas.values()],
      resumen,
      insightObservacion: insights.observacion,
      insightAccion: insights.accion,
      fuente: 'ms7',
    };
  }

  private loadFallbackAsync(
    periodosEscolares: ReportePeriodoEscolarItem[],
    materiasLoad: { materias: MateriaDocenteItem[]; periodoActivoNombre: string | null },
    historial: ReporteExportacionItem[],
  ): Observable<ReportesDocenteData> {
    const materias = materiasLoad.materias;
    if (!materias.length) {
      return of({
        ...this.buildEmpty(periodosEscolares, materiasLoad.periodoActivoNombre),
        historial,
        fuente: 'empty',
      });
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
          periodosEscolares.find((p) => p.activo)?.nombre ||
          'Periodo activo';

        const historialAcademico: ReporteAcademicoPeriodoItem[] = [
          {
            periodo: periodoActivoNombre,
            activo: true,
            resumen: this.buildResumenPeriodo(materiasStats),
            materias: materiasStats,
          },
          ...periodosEscolares
            .filter((p) => !p.activo)
            .map((p) => ({
              periodo: p.nombre,
              activo: false,
              resumen: 'Sin datos en MS-7 para este periodo. Revise proyecciones o use el periodo activo.',
              materias: [] as ReporteAcademicoMateriaItem[],
            })),
        ];

        const materiasComparadas = this.buildComparativas(historialAcademico);
        const resumen = this.buildResumen(materiasStats);
        const insights = this.buildInsights(materiasStats);

        return {
          periodosEscolares,
          historial,
          historialAcademico,
          materiasComparadas,
          materiasOpciones: materias.map((m) => ({
            id: m.id,
            label: `${m.materia} · NRC ${m.nrc}`,
          })),
          resumen,
          insightObservacion: insights.observacion,
          insightAccion:
            'MS-7 sin proyecciones: ejecute rebuild_report_projections --from-backfill o espere eventos del bus.',
          fuente: 'fallback' as const,
        };
      }),
    );
  }

  private buildHistorialFromStats(
    rows: StatsPeriodoApiDto[],
    periodosEscolares: ReportePeriodoEscolarItem[],
    labelByMateriaId: Map<number, string>,
  ): ReporteAcademicoPeriodoItem[] {
    const porPeriodo = new Map<string, ReporteAcademicoMateriaItem[]>();

    for (const row of rows) {
      const key = row.periodo_nombre?.trim() || 'Sin periodo';
      const list = porPeriodo.get(key) ?? [];
      list.push(this.mapStatsRow(row, labelByMateriaId));
      porPeriodo.set(key, list);
    }

    const nombresConocidos = new Set(periodosEscolares.map((p) => p.nombre));
    const resultado: ReporteAcademicoPeriodoItem[] = periodosEscolares.map((pe) => {
      const materias = porPeriodo.get(pe.nombre) ?? [];
      return {
        periodo: pe.nombre,
        activo: pe.activo,
        resumen: materias.length
          ? this.buildResumenPeriodo(materias)
          : pe.activo
            ? 'Sin materias con estadísticas en MS-7 para el periodo activo.'
            : 'Sin materias registradas en MS-7 para este periodo.',
        materias,
      };
    });

    for (const [periodo, materias] of porPeriodo) {
      if (!nombresConocidos.has(periodo)) {
        resultado.push({
          periodo,
          activo: false,
          resumen: this.buildResumenPeriodo(materias),
          materias,
        });
      }
    }

    return resultado.sort((a, b) => {
      if (a.activo !== b.activo) {
        return a.activo ? -1 : 1;
      }
      return a.periodo.localeCompare(b.periodo);
    });
  }

  private mapStatsRow(
    row: StatsPeriodoApiDto,
    labelByMateriaId: Map<number, string>,
  ): ReporteAcademicoMateriaItem {
    const total = Number(row.total_alumnos) || 0;
    const aprobados = Number(row.aprobados) || 0;
    const aprobacion = total > 0 ? Math.round((aprobados / total) * 100) : 0;
    const label = labelByMateriaId.get(row.materia_id);
    const grupo = label?.includes('NRC') ? label.split('·').pop()?.trim() ?? `ID ${row.materia_id}` : `ID ${row.materia_id}`;

    return {
      materiaId: row.materia_id,
      nombre: row.materia_nombre,
      grupo,
      alumnos: total,
      promedio: Number(row.promedio_grupal) || 0,
      aprobacion,
    };
  }

  private mapComparativaMs7(comparativa: ComparativaMateriaApiDto[]): ReporteComparativaItem[] {
    const items: ReporteComparativaItem[] = [];

    for (const grupo of comparativa) {
      if (!grupo.periodos || grupo.periodos.length < 2) {
        continue;
      }
      const ordenados = [...grupo.periodos].sort((a, b) =>
        (a.periodo_nombre || '').localeCompare(b.periodo_nombre || ''),
      );
      const anterior = ordenados[ordenados.length - 2];
      const actual = ordenados[ordenados.length - 1];
      const aprobacionAnterior = this.aprobacionFromStats(anterior);
      const aprobacionActual = this.aprobacionFromStats(actual);
      const promedioAnterior = Number(anterior.promedio_grupal) || 0;
      const promedioActual = Number(actual.promedio_grupal) || 0;

      items.push({
        nombre: grupo.materia_nombre || actual.materia_nombre,
        repeticiones: ordenados.length,
        promedioActual,
        promedioAnterior,
        variacionPromedio: this.formatVariacion(promedioActual - promedioAnterior),
        aprobacionActual,
        aprobacionAnterior,
        variacionAprobacion: this.formatVariacion(aprobacionActual - aprobacionAnterior, true),
        periodos: ordenados.map((p) => p.periodo_nombre || 'Sin periodo'),
      });
    }

    return items;
  }

  private aprobacionFromStats(row: StatsPeriodoApiDto): number {
    const total = Number(row.total_alumnos) || 0;
    const aprobados = Number(row.aprobados) || 0;
    return total > 0 ? Math.round((aprobados / total) * 100) : 0;
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
      insightAccion: 'Importa tu programación de materias o revisa el periodo activo.',
      fuente: 'empty',
    };
  }

  private buildSinSesion(): ReportesDocenteData {
    return {
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
      insightObservacion: 'Inicia sesión como docente para ver reportes.',
      insightAccion: 'Vuelve a iniciar sesión si el token expiró.',
      fuente: 'empty',
    };
  }

  private buildErrorLoad(): ReportesDocenteData {
    return {
      periodosEscolares: [],
      historial: this.getHistorialExportaciones(),
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
      insightAccion: 'Verifica que MS-7, MS-2 y el gateway Nginx (:8080) estén activos.',
      fuente: 'empty',
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
      materiaId: materia.id,
      nombre: materia.materia,
      grupo: materia.seccion || materia.clave || materia.nrc,
      alumnos: total || alumnosInscritos,
      promedio,
      aprobacion,
    };
  }

  private buildResumenPeriodo(materias: ReporteAcademicoMateriaItem[]): string {
    if (!materias.length) {
      return 'Sin materias en el periodo.';
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
        observacion: 'Sin estadísticas del docente en MS-7 para el periodo activo.',
        accion: 'Captura calificaciones y confirma asistencias; luego sincroniza proyecciones MS-7.',
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
