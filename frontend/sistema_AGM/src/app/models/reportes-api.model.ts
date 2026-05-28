/** DTOs REST de MS-7 (Reportes y estadísticas). */

export interface StatsPeriodoApiDto {
  periodo_nombre: string;
  periodo_id: number | null;
  materia_nombre: string;
  materia_id: number;
  total_alumnos: number;
  aprobados: number;
  reprobados: number;
  promedio_grupal: number;
  porcentaje_asistencia: number | null;
}

export interface ComparativaMateriaApiDto {
  materia_nombre: string;
  periodos: StatsPeriodoApiDto[];
}

export interface EstadisticasDocenteApiDto {
  docente_id: number;
  periodos: StatsPeriodoApiDto[];
  comparativa: ComparativaMateriaApiDto[];
}

export type ReporteDescargaFormato = 'pdf' | 'xlsx';
export type ReporteDescargaTipo = 'calificaciones' | 'asistencias';
