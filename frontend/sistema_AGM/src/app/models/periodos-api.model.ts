/** DTOs REST de MS-2 (Periodos & Materias). */

export interface PeriodoApiDto {
  id: number;
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  plan_estudios: string;
  activo: boolean;
  fecha_creacion?: string;
  fecha_actualizacion?: string;
}

export interface MateriaApiDto {
  id: number;
  periodo: number;
  nrc: string;
  nombre: string;
  seccion: string;
  clave: string;
  docente_nombre: string;
  docente_id?: number | null;
  horario: string;
  fecha_creacion?: string;
}

export interface ImportarMateriasResultDto {
  creadas: number;
  actualizadas: number;
  errores: number;
}
