/** Contrato envelope REST de microservicios AGM (MS-1). */

export interface AgmUser {
  id: number;
  email: string;
  nombre: string;
  rol: 'admin' | 'docente' | 'alumno' | string;
  activo?: boolean;
}

export interface AgmApiResponse<T> {
  success: boolean;
  data: T | null;
  message: string;
  errors?: Record<string, string[]>;
}

export interface LoginData {
  access_token: string;
  refresh_token: string;
  user: AgmUser;
}

export interface RefreshTokenData {
  access: string;
  refresh?: string;
}
