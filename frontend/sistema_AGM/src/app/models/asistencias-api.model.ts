/** DTOs REST de MS-5 (Asistencias QR). */

export interface SesionAsistenciaApiDto {
  id: number;
  materia_id: number;
  docente_id: number;
  fecha_inicio: string;
  fecha_fin_teorica: string;
  estado: string;
  activa: boolean;
  minutos_transcurridos?: number;
  vigente?: boolean;
}

export interface IniciarSesionResponse {
  message: string;
  sesion: SesionAsistenciaApiDto;
}

export interface SesionActivaResponse {
  activa: boolean;
  sesion: SesionAsistenciaApiDto | null;
  message?: string;
}

export interface ConfirmarSesionResponse {
  message: string;
  sesion: SesionAsistenciaApiDto;
}

export interface RegistroAsistenciaApiDto {
  id: number;
  alumno_id: number;
  estado: 'presente' | 'retardo' | 'ausente' | string;
  minuto_registro: number;
  fecha_registro: string;
}

export interface RegistrarAsistenciaResponse {
  exitoso: boolean;
  alumno_id: number;
  sesion_id: number;
  estado: string;
  minuto_registro: number;
  mensaje: string;
}

export interface QrGenerateResponse {
  payload: Record<string, unknown>;
  encoded_payload: string;
  expires_in: number;
  qr_hash: string;
  sesion_id: number;
}

export interface SesionHistorialItemDto {
  sesion_id: number;
  fecha_inicio: string;
  fecha_fin_teorica: string;
  estado: string;
  activa: boolean;
  total_registros: number;
  presentes: number;
  retardos: number;
}

export interface SesionesHistorialResponse {
  materia_id: number;
  dias: number;
  sesiones: SesionHistorialItemDto[];
}

export interface StatsSesionResponse {
  sesion_id: number;
  materia_id: number;
  docente_id?: number;
  presentes: number;
  retardos: number;
  ausentes: number;
  total_registrados: number;
  estado_sesion?: string;
  vigente?: boolean;
  minutos_transcurridos?: number;
  fecha_inicio?: string;
  fecha_fin_teorica?: string;
}

export interface StatsAlumnoMateriaResponse {
  alumno_id: number;
  materia_id: number;
  total_registros: number;
  presentes: number;
  retardos: number;
  ausentes: number;
  porcentaje_asistencia: number;
  porcentaje_retardo: number;
}

export interface AlumnoMateriaAsistenciaResponse {
  alumno_id: number;
  materia_id: number;
  total_registros: number;
  presentes: number;
  retardos: number;
  ausentes: number;
  porcentaje_asistencia: number;
  registros: RegistroAsistenciaApiDto[];
}
