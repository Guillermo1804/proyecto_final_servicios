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

export interface ImportarAlumnosPreviewDto {
  validas: Record<string, unknown>[];
  errores: Record<string, unknown>[];
  total_validas: number;
  total_errores: number;
}

export interface ImportarAlumnosConfirmarDto {
  creados: number;
  actualizados: number;
}

export interface ImportarDocentesResultDto {
  creados: number;
  omitidos: number;
  errores: number;
  detalle_errores?: Record<string, unknown>[];
}
