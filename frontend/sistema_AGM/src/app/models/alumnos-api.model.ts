/** DTOs REST de MS-3 (Docentes & Alumnos). */

export interface DocenteApiDto {
  id: number;
  usuario_id: number | null;
  nombre: string;
  apellido: string;
  email: string;
  departamento: string;
  fecha_creacion?: string;
}

export interface AlumnoApiDto {
  id: number;
  usuario_id: number | null;
  matricula: string;
  nombre: string;
  apellido: string;
  email: string;
  carrera: string;
  semestre: number;
  activo: boolean;
  fecha_creacion?: string;
}

export interface InscripcionMateriaApiDto {
  id: number;
  materia_id: number;
  nrc: string;
  nombre_materia: string;
  docente_nombre: string;
  horario: string;
  activa: boolean;
  fecha_inscripcion?: string;
  alumno: AlumnoApiDto;
  materia_detail?: Record<string, unknown>;
}

export type AlumnoImportPreviewAccion = 'nuevo' | 'actualizar';
export type AlumnoImportPreviewInscripcion = 'nueva' | 'ya_inscrito' | 'reactivar';

export interface AlumnoImportPreviewFilaDto {
  matricula: string;
  nombre: string;
  apellido: string;
  email: string;
  carrera?: string;
  semestre?: number;
  nombre_completo?: string;
  accion: AlumnoImportPreviewAccion;
  inscripcion: AlumnoImportPreviewInscripcion;
  email_actual?: string;
  tiene_usuario_ms1?: boolean;
}

export interface AlumnoImportPreviewResumenDto {
  total: number;
  nuevos: number;
  actualizados: number;
  inscripciones_nuevas: number;
  ya_inscritos: number;
  con_email: number;
  sin_email: number;
}

export interface ImportarAlumnosPreviewDto {
  filas: AlumnoImportPreviewFilaDto[];
  resumen: AlumnoImportPreviewResumenDto;
  errores_parseo: number;
  nrc_pdf?: string;
  nombre_materia_pdf?: string;
  docente_pdf?: string;
  periodo_pdf?: string;
  advertencias?: Array<{ error?: string } | Record<string, unknown>>;
}

export interface ImportarAlumnosPdfResultDto {
  creados: number;
  actualizados: number;
  inscritos: number;
  errores: number;
  filas_leidas: number;
  errores_parseo: number;
  nrc_pdf?: string;
  nombre_materia_pdf?: string;
  detalle_errores?: Array<{ error?: string } | Record<string, unknown>>;
}

export interface ImportarDocentesResultDto {
  creados: number;
  omitidos: number;
  errores: number;
  filas_leidas?: number;
  errores_parseo?: number;
  detalle_errores?: Array<{ error?: string } | Record<string, unknown>>;
}
