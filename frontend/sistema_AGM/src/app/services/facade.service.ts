import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, of, tap } from 'rxjs';
import { ErrorsService } from './tools/errors.service';
import { ValidatorService } from './tools/validator.service';
import { environment } from '../../environments/environment';

const jsonHeaders = new HttpHeaders({ 'Content-Type': 'application/json' });

const ACCESS_TOKEN_KEY = 'agm_access_token';
const REFRESH_TOKEN_KEY = 'agm_refresh_token';

export interface AgmEnvelope<T = unknown> {
  success?: boolean;
  data?: T;
  message?: string;
  errors?: Record<string, unknown>;
}

export interface AuthUser {
  id?: number;
  email?: string;
  nombre?: string;
  rol?: string;
  activo?: boolean;
}

interface AuthResponse {
  success?: boolean;
  data?: {
    access_token?: string;
    refresh_token?: string;
    user?: AuthUser;
  };
  access_token?: string;
  refresh_token?: string;
  message?: string;
}

@Injectable({
  providedIn: 'root',
})
export class FacadeService {
  constructor(
    private http: HttpClient,
    public router: Router,
    private validatorService: ValidatorService,
    private errorService: ErrorsService,
  ) {}

  // ── Auth (MS-1) ─────────────────────────────────────────────────────

  public validarLogin(username: string, password: string): Record<string, string> {
    const data = { username, password };
    const error: Record<string, string> = {};
    if (!this.validatorService.required(data.username)) {
      error.username = this.errorService.required;
    } else if (!this.validatorService.max(data.username, 40)) {
      error.username = this.errorService.max(40);
    } else if (!this.validatorService.email(data.username)) {
      error.username = this.errorService.email;
    }
    if (!this.validatorService.required(data.password)) {
      error.password = this.errorService.required;
    }
    return error;
  }

  public login(username: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(
      this.buildApiUrl('/auth/login'),
      { email: username, password },
      { headers: jsonHeaders },
    );
  }

  public logout(): Observable<AgmEnvelope<null>> {
    const refresh = this.getRefreshToken();
    if (!refresh) {
      this.clearSession();
      return of({ success: true, data: null });
    }
    return this.http
      .post<AgmEnvelope<null>>(
        this.buildApiUrl('/auth/logout'),
        { refresh },
        { headers: this.authHeaders() },
      )
      .pipe(tap(() => this.clearSession()));
  }

  public getMe(): Observable<AgmEnvelope<AuthUser>> {
    return this.http.get<AgmEnvelope<AuthUser>>(this.buildApiUrl('/auth/me'), {
      headers: this.authHeaders(),
    });
  }

  public storeTokens(response: AuthResponse, remember = false): string | null {
    const accessToken = this.extractAccessToken(response);
    const refreshToken = this.extractRefreshToken(response);
    if (!accessToken) {
      return null;
    }
    const primary = remember ? localStorage : sessionStorage;
    const secondary = remember ? sessionStorage : localStorage;
    primary.setItem(ACCESS_TOKEN_KEY, accessToken);
    secondary.removeItem(ACCESS_TOKEN_KEY);
    if (refreshToken) {
      primary.setItem(REFRESH_TOKEN_KEY, refreshToken);
      secondary.removeItem(REFRESH_TOKEN_KEY);
    }
    if (response?.data?.user?.rol) {
      primary.setItem('user_role', response.data.user.rol);
    }
    if (response?.data?.user?.id != null) {
      primary.setItem('user_id', String(response.data.user.id));
    }
    return accessToken;
  }

  public getAccessToken(): string | null {
    return sessionStorage.getItem(ACCESS_TOKEN_KEY) || localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  public getRefreshToken(): string | null {
    return sessionStorage.getItem(REFRESH_TOKEN_KEY) || localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  public clearSession(): void {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_id');
  }

  public isAuthenticated(): boolean {
    return Boolean(this.getAccessToken());
  }

  public getUserId(): number | null {
    const fromStorage = localStorage.getItem('user_id') || sessionStorage.getItem('user_id');
    if (fromStorage) {
      return Number(fromStorage);
    }
    const payload = this.getJwtPayload(this.getAccessToken());
    const id = payload?.['user_id'] ?? payload?.['sub'];
    return id != null ? Number(id) : null;
  }

  public getUserRole(): string | null {
    const payload = this.getJwtPayload(this.getAccessToken());
    const roleFromJwt =
      payload?.['rol'] ?? payload?.['role'] ?? payload?.['user']?.['rol'];
    if (roleFromJwt) {
      return this.normalizeRole(roleFromJwt);
    }
    const stored = sessionStorage.getItem('user_role') || localStorage.getItem('user_role');
    return this.normalizeRole(stored);
  }

  public resolveHomeRoute(role: string | null): string {
    const r = this.normalizeRole(role);
    if (r === 'admin') return '/admin/dashboard';
    if (r === 'docente') return '/docente/dashboard';
    if (r === 'alumno') return '/alumno/dashboard';
    return '/login';
  }

  // ── Periodos & Materias (MS-2) ──────────────────────────────────────

  public listPeriodos(page = 1, limit = 50): Observable<AgmEnvelope<unknown>> {
    const params = new HttpParams().set('page', page).set('limit', limit);
    return this.http.get<AgmEnvelope<unknown>>(this.buildApiUrl('/periodos/'), {
      headers: this.authHeaders(),
      params,
    });
  }

  public getPeriodoActivo(): Observable<AgmEnvelope<unknown>> {
    return this.http.get<AgmEnvelope<unknown>>(this.buildApiUrl('/periodos/activo/'), {
      headers: this.authHeaders(),
    });
  }

  public listMaterias(query: Record<string, string | number> = {}): Observable<AgmEnvelope<unknown>> {
    let params = new HttpParams();
    Object.entries(query).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        params = params.set(k, String(v));
      }
    });
    return this.http.get<AgmEnvelope<unknown>>(this.buildApiUrl('/materias/'), {
      headers: this.authHeaders(),
      params,
    });
  }

  public createPeriodo(payload: {
    nombre: string;
    fecha_inicio: string;
    fecha_fin: string;
    plan_estudios?: string;
  }): Observable<AgmEnvelope<unknown>> {
    return this.http.post<AgmEnvelope<unknown>>(this.buildApiUrl('/periodos/'), payload, {
      headers: this.authHeaders(),
    });
  }

  public activarPeriodo(periodoId: number): Observable<AgmEnvelope<unknown>> {
    return this.http.post<AgmEnvelope<unknown>>(
      this.buildApiUrl(`/periodos/${periodoId}/activar/`),
      {},
      { headers: this.authHeaders() },
    );
  }

  public importarMateriasPdf(periodoId: number, file: File): Observable<AgmEnvelope<unknown>> {
    const form = new FormData();
    form.append('archivo', file);
    return this.http.post<AgmEnvelope<unknown>>(
      this.buildApiUrl(`/periodos/${periodoId}/importar-materias/`),
      form,
      { headers: this.authHeaders() },
    );
  }

  public createMateria(payload: Record<string, unknown>): Observable<AgmEnvelope<unknown>> {
    return this.http.post<AgmEnvelope<unknown>>(this.buildApiUrl('/materias/'), payload, {
      headers: this.authHeaders(),
    });
  }

  // ── Alumnos (MS-3) ──────────────────────────────────────────────────

  public getMisMateriasAlumno(): Observable<AgmEnvelope<unknown>> {
    return this.http.get<AgmEnvelope<unknown>>(this.buildApiUrl('/alumnos/me/materias/'), {
      headers: this.authHeaders(),
    });
  }

  public listDocentes(query: Record<string, string | number> = {}): Observable<AgmEnvelope<unknown>> {
    let params = new HttpParams();
    Object.entries(query).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        params = params.set(k, String(v));
      }
    });
    return this.http.get<AgmEnvelope<unknown>>(this.buildApiUrl('/docentes/'), {
      headers: this.authHeaders(),
      params,
    });
  }

  public importDocentesPdf(file: File): Observable<AgmEnvelope<unknown>> {
    const form = new FormData();
    form.append('file', file);
    return this.http.post<AgmEnvelope<unknown>>(this.buildApiUrl('/docentes/importar/'), form, {
      headers: this.authHeaders(),
    });
  }

  public previewImportAlumnos(file: File): Observable<AgmEnvelope<unknown>> {
    const form = new FormData();
    form.append('archivo', file);
    return this.http.post<AgmEnvelope<unknown>>(
      this.buildApiUrl('/alumnos/importar/preview/'),
      form,
      { headers: this.authHeaders() },
    );
  }

  public confirmImportAlumnos(
    alumnos: Record<string, unknown>[],
    materiaId?: number,
  ): Observable<AgmEnvelope<unknown>> {
    const body: { alumnos: Record<string, unknown>[]; materia_id?: number } = { alumnos };
    if (materiaId) {
      body.materia_id = materiaId;
    }
    return this.http.post<AgmEnvelope<unknown>>(
      this.buildApiUrl('/alumnos/importar/confirmar/'),
      body,
      { headers: this.authHeaders() },
    );
  }

  public listAlumnosPorMateria(materiaId: number): Observable<AgmEnvelope<unknown>> {
    const params = new HttpParams().set('materia_id', materiaId);
    return this.http.get<AgmEnvelope<unknown>>(this.buildApiUrl('/alumnos/por-materia/'), {
      headers: this.authHeaders(),
      params,
    });
  }

  // ── Calificaciones (MS-4) ───────────────────────────────────────────

  public getConcentrado(materiaId: number): Observable<AgmEnvelope<unknown>> {
    return this.http.get<AgmEnvelope<unknown>>(
      this.buildApiUrl(`/concentrado/${materiaId}`),
      { headers: this.authHeaders() },
    );
  }

  public getPonderaciones(materiaId: number): Observable<AgmEnvelope<unknown>> {
    return this.http.get<AgmEnvelope<unknown>>(
      this.buildApiUrl(`/ponderaciones/${materiaId}`),
      { headers: this.authHeaders() },
    );
  }

  public savePonderaciones(
    materiaId: number,
    ponderaciones: { nombre_categoria: string; porcentaje: string }[],
  ): Observable<AgmEnvelope<unknown>> {
    return this.http.post<AgmEnvelope<unknown>>(
      this.buildApiUrl(`/ponderaciones/${materiaId}`),
      { ponderaciones },
      { headers: this.authHeaders() },
    );
  }

  public listActividades(materiaId: number): Observable<AgmEnvelope<unknown>> {
    const params = new HttpParams().set('materia', materiaId);
    return this.http.get<AgmEnvelope<unknown>>(this.buildApiUrl('/actividades/'), {
      headers: this.authHeaders(),
      params,
    });
  }

  public upsertCalificacion(payload: {
    actividad_id: number;
    alumno_id: number;
    calificacion: string | number;
  }): Observable<AgmEnvelope<unknown>> {
    return this.http.post<AgmEnvelope<unknown>>(this.buildApiUrl('/calificaciones/'), payload, {
      headers: this.authHeaders(),
    });
  }

  public importCalificacionesExcel(materiaId: number, file: File): Observable<AgmEnvelope<unknown>> {
    const form = new FormData();
    form.append('archivo', file);
    return this.http.post<AgmEnvelope<unknown>>(
      this.buildApiUrl(`/calificaciones/importar/${materiaId}`),
      form,
      { headers: this.authHeaders() },
    );
  }

  public cerrarMateriaCalificaciones(materiaId: number): Observable<AgmEnvelope<unknown>> {
    return this.http.post<AgmEnvelope<unknown>>(
      this.buildApiUrl(`/materias/${materiaId}/cerrar`),
      {},
      { headers: this.authHeaders() },
    );
  }

  public imprimirListaCalificaciones(materiaId: number): Observable<AgmEnvelope<unknown>> {
    return this.http.post<AgmEnvelope<unknown>>(
      this.buildApiUrl(`/materias/${materiaId}/imprimir-lista`),
      {},
      { headers: this.authHeaders() },
    );
  }

  // ── Asistencias (MS-5) ────────────────────────────────────────────────

  public iniciarSesionAsistencia(
    materiaId: number,
    docenteId: number,
  ): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(
      this.buildApiUrl('/sesiones/iniciar/'),
      { materia_id: materiaId, docente_id: docenteId },
      { headers: this.authHeaders() },
    );
  }

  public getSesionActiva(materiaId: number): Observable<Record<string, unknown>> {
    const params = new HttpParams().set('materia_id', materiaId);
    return this.http.get<Record<string, unknown>>(this.buildApiUrl('/sesiones/activa/'), {
      headers: this.authHeaders(),
      params,
    });
  }

  public getSesionStats(sesionId: number): Observable<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(
      this.buildApiUrl(`/sesiones/${sesionId}/stats/`),
      { headers: this.authHeaders() },
    );
  }

  public cerrarSesionAsistencia(sesionId: number): Observable<Record<string, unknown>> {
    return this.http.delete<Record<string, unknown>>(
      this.buildApiUrl(`/sesiones/${sesionId}/cerrar/`),
      { headers: this.authHeaders() },
    );
  }

  public listRegistrosAsistencia(sesionId: number): Observable<unknown[]> {
    const params = new HttpParams().set('sesion_id', sesionId);
    return this.http.get<unknown[]>(this.buildApiUrl('/registros/'), {
      headers: this.authHeaders(),
      params,
    });
  }

  public registrarAsistenciaQr(encodedPayload: string): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(
      this.buildApiUrl('/asistencias/registrar/'),
      { encoded_payload: encodedPayload },
      { headers: this.authHeaders() },
    );
  }

  public registrosAsistenciaHoy(materiaId: number): Observable<unknown[]> {
    const params = new HttpParams().set('materia_id', materiaId);
    return this.http.get<unknown[]>(this.buildApiUrl('/registros/por_materia_hoy/'), {
      headers: this.authHeaders(),
      params,
    });
  }

  // ── Reportes & estadísticas (MS-7) ────────────────────────────────────

  public downloadReporte(
    tipo: 'calificaciones' | 'asistencias',
    materiaId: number,
    formato: 'pdf' | 'xlsx',
  ): Observable<Blob> {
    const params = new HttpParams().set('formato', formato);
    return this.http.get(this.buildApiUrl(`/reportes/${tipo}/${materiaId}`), {
      headers: this.authHeaders(),
      params,
      responseType: 'blob',
    });
  }

  public getEstadisticasDocente(docenteUsuarioId: number): Observable<AgmEnvelope<unknown>> {
    return this.http.get<AgmEnvelope<unknown>>(
      this.buildApiUrl(`/estadisticas/docente/${docenteUsuarioId}`),
      { headers: this.authHeaders() },
    );
  }

  public getEstadisticasAlumno(alumnoId: number): Observable<AgmEnvelope<unknown>> {
    return this.http.get<AgmEnvelope<unknown>>(
      this.buildApiUrl(`/estadisticas/alumno/${alumnoId}`),
      { headers: this.authHeaders() },
    );
  }

  /** Extrae array de envelope paginado o plano. */
  public extractList<T>(body: AgmEnvelope<unknown> | null | undefined): T[] {
    if (body?.success === false) {
      return [];
    }
    const data = body?.data;
    if (Array.isArray(data)) {
      return data as T[];
    }
    if (data && typeof data === 'object' && Array.isArray((data as { results?: T[] }).results)) {
      return (data as { results: T[] }).results;
    }
    return [];
  }

  public triggerDownload(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  private authHeaders(): HttpHeaders {
    const token = this.getAccessToken();
    if (!token) {
      return jsonHeaders;
    }
    return jsonHeaders.set('Authorization', `Bearer ${token}`);
  }

  private buildApiUrl(path: string): string {
    const baseUrl = environment.apiBaseUrl || environment.url_api || '';
    return `${baseUrl.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
  }

  private extractAccessToken(response: AuthResponse): string | null {
    return (
      response?.data?.access_token ??
      response?.access_token ??
      (response as { access?: string }).access ??
      (response as { token?: string }).token ??
      null
    );
  }

  private extractRefreshToken(response: AuthResponse): string | null {
    return (
      response?.data?.refresh_token ??
      response?.refresh_token ??
      (response as { refresh?: string }).refresh ??
      null
    );
  }

  private getJwtPayload(token: string | null): Record<string, unknown> | null {
    if (!token) return null;
    const parts = token.split('.');
    if (parts.length < 2) return null;
    try {
      const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=');
      return JSON.parse(atob(padded)) as Record<string, unknown>;
    } catch {
      return null;
    }
  }

  private normalizeRole(role: string | null | undefined): string | null {
    if (!role) return null;
    return String(role).trim().toLowerCase();
  }
}
