/** DTOs REST de MS-4 (Calificaciones & Ponderaciones). */

export interface PonderacionApiDto {
  id: number;
  materia_id: number;
  nombre_categoria: string;
  porcentaje: string | number;
}

export interface PonderacionesMateriaDto {
  materia_id: number;
  ponderaciones: PonderacionApiDto[];
  total: string | number;
}

export interface ActividadApiDto {
  id: number;
  ponderacion_id: number;
  categoria_nombre: string;
  categoria_porcentaje: string | number;
  nombre: string;
  descripcion: string;
  fecha: string | null;
}

export interface ActividadesPorCategoriaDto {
  categoria_nombre: string;
  categoria_porcentaje: string | number;
  actividades: ActividadApiDto[];
}

export interface ActividadesMateriaDto {
  materia_id: number;
  categorias: ActividadesPorCategoriaDto[];
}

export interface CalificacionActividadDto {
  actividad_id: number;
  actividad_nombre?: string;
  categoria?: string;
  calificacion: string | number;
}

export interface AlumnoConcentradoDto {
  alumno_id: number;
  matricula: string;
  nombre: string;
  calificaciones: CalificacionActividadDto[];
  promedio_real: string | number;
  promedio_redondeado: number;
}

export interface ConcentradoMateriaDto {
  materia_id: number;
  categorias: Array<{
    nombre: string;
    porcentaje: string | number;
    actividades: Array<{ id: number; nombre: string }>;
  }>;
  alumnos: AlumnoConcentradoDto[];
}

export interface CalificacionOutputDto {
  id: number;
  actividad_id: number;
  alumno_id: number;
  calificacion: string | number;
}

export interface ImportarCalificacionesResumenDto {
  procesadas: number;
  importadas: number;
  fallos: number;
  ok?: number;
  errores: Array<{ fila?: number; motivo?: string }>;
}
