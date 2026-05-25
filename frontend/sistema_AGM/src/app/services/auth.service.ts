import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, of, throwError } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';

import { environment } from '../../environments/environment';
import {
  AgmApiResponse,
  AgmUser,
  LoginData,
  RefreshTokenData,
} from '../models/auth-api.model';

const httpOptions = {
  headers: new HttpHeaders({ 'Content-Type': 'application/json' }),
};

const ACCESS_TOKEN_KEY = 'agm_access_token';
const REFRESH_TOKEN_KEY = 'agm_refresh_token';
const USER_ID_KEY = 'agm_user_id';
const USER_ROLE_KEY = 'agm_user_role';
const USER_NAME_KEY = 'agm_user_nombre';
const USER_EMAIL_KEY = 'agm_user_email';

/**
 * Integracion frontend <-> MS-1 Auth (via Nginx :8080 o MS-1 :8001).
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly apiBase =
    environment.apiBaseUrl || environment.url_api || 'http://127.0.0.1:8080';

  constructor(
    private http: HttpClient,
    private router: Router,
  ) {}

  login(email: string, password: string): Observable<AgmApiResponse<LoginData>> {
    return this.http.post<AgmApiResponse<LoginData>>(
      this.url('/auth/login'),
      { email, password },
      httpOptions,
    );
  }

  refreshToken(): Observable<AgmApiResponse<RefreshTokenData>> {
    const refresh = this.getRefreshToken();
    if (!refresh) {
      return throwError(() => new Error('No refresh token'));
    }
    return this.http.post<AgmApiResponse<RefreshTokenData>>(
      this.url('/auth/refresh-token'),
      { refresh },
      httpOptions,
    );
  }

  getMe(): Observable<AgmApiResponse<AgmUser>> {
    return this.http.get<AgmApiResponse<AgmUser>>(this.url('/auth/me'));
  }

  logoutRemote(): Observable<AgmApiResponse<null>> {
    const refresh = this.getRefreshToken();
    if (!refresh) {
      return of({ success: true, data: null, message: 'Sesion local cerrada' });
    }
    return this.http.post<AgmApiResponse<null>>(
      this.url('/auth/logout'),
      { refresh },
      httpOptions,
    ).pipe(catchError(() => of({ success: true, data: null, message: 'Sesion cerrada' })));
  }

  forgotPassword(email: string): Observable<AgmApiResponse<null>> {
    return this.http.post<AgmApiResponse<null>>(
      this.url('/auth/forgot-password'),
      { email },
      httpOptions,
    );
  }

  resetPassword(token: string, password: string): Observable<AgmApiResponse<null>> {
    return this.http.post<AgmApiResponse<null>>(
      this.url('/auth/reset-password'),
      { token, password },
      httpOptions,
    );
  }

  /** Persiste tokens y perfil tras login exitoso. */
  storeSession(loginData: LoginData, remember = false): boolean {
    const storage = remember ? localStorage : sessionStorage;
    const other = remember ? sessionStorage : localStorage;

    if (!loginData?.access_token) {
      return false;
    }

    storage.setItem(ACCESS_TOKEN_KEY, loginData.access_token);
    other.removeItem(ACCESS_TOKEN_KEY);

    if (loginData.refresh_token) {
      storage.setItem(REFRESH_TOKEN_KEY, loginData.refresh_token);
      other.removeItem(REFRESH_TOKEN_KEY);
    }

    const user = loginData.user;
    if (user) {
      storage.setItem(USER_ID_KEY, String(user.id));
      storage.setItem(USER_ROLE_KEY, user.rol);
      storage.setItem(USER_NAME_KEY, user.nombre);
      storage.setItem(USER_EMAIL_KEY, user.email);
      other.removeItem(USER_ID_KEY);
      other.removeItem(USER_ROLE_KEY);
      other.removeItem(USER_NAME_KEY);
      other.removeItem(USER_EMAIL_KEY);
    }

    return true;
  }

  applyRefreshedAccess(access: string): void {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, access);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
  }

  getAccessToken(): string | null {
    return (
      sessionStorage.getItem(ACCESS_TOKEN_KEY) ||
      localStorage.getItem(ACCESS_TOKEN_KEY)
    );
  }

  getRefreshToken(): string | null {
    return (
      sessionStorage.getItem(REFRESH_TOKEN_KEY) ||
      localStorage.getItem(REFRESH_TOKEN_KEY)
    );
  }

  getStoredUser(): Partial<AgmUser> | null {
    const id = sessionStorage.getItem(USER_ID_KEY) || localStorage.getItem(USER_ID_KEY);
    if (!id) {
      return null;
    }
    return {
      id: Number(id),
      rol: this.getUserRole() || '',
      nombre: sessionStorage.getItem(USER_NAME_KEY) || localStorage.getItem(USER_NAME_KEY) || '',
      email: sessionStorage.getItem(USER_EMAIL_KEY) || localStorage.getItem(USER_EMAIL_KEY) || '',
    };
  }

  clearSession(): void {
    for (const key of [
      ACCESS_TOKEN_KEY,
      REFRESH_TOKEN_KEY,
      USER_ID_KEY,
      USER_ROLE_KEY,
      USER_NAME_KEY,
      USER_EMAIL_KEY,
      'user_role',
    ]) {
      sessionStorage.removeItem(key);
      localStorage.removeItem(key);
    }
  }

  isAuthenticated(): boolean {
    return Boolean(this.getAccessToken());
  }

  getUserRole(): string | null {
    const payload = this.decodeJwt(this.getAccessToken());
    const userClaim = payload?.['user'] as Record<string, unknown> | undefined;
    const fromJwt =
      payload?.['rol'] ??
      payload?.['role'] ??
      userClaim?.['rol'];
    if (fromJwt) {
      return this.normalizeRole(String(fromJwt));
    }
    const stored =
      sessionStorage.getItem(USER_ROLE_KEY) || localStorage.getItem(USER_ROLE_KEY);
    return this.normalizeRole(stored);
  }

  resolveHomeRoute(role: string | null): string {
    const r = this.normalizeRole(role);
    if (r === 'admin') return '/admin/dashboard';
    if (r === 'docente') return '/docente/dashboard';
    if (r === 'alumno') return '/alumno/dashboard';
    return '/login';
  }

  logout(): void {
    this.logoutRemote()
      .pipe(tap(() => this.clearSession()))
      .subscribe({
        next: () => this.router.navigate(['/login']),
        error: () => {
          this.clearSession();
          this.router.navigate(['/login']);
        },
      });
  }

  refreshTokenAndStore(): Observable<string | null> {
    return this.refreshToken().pipe(
      map((resp) => {
        const access = resp?.data?.access;
        if (resp?.success && access) {
          this.applyRefreshedAccess(access);
          return access;
        }
        return null;
      }),
    );
  }

  private url(path: string): string {
    return `${this.apiBase.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
  }

  private decodeJwt(token: string | null): Record<string, unknown> | null {
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
