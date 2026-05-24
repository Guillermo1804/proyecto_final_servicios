import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { ErrorsService } from './tools/errors.service';
import { ValidatorService } from './tools/validator.service';

import { environment } from '../../environments/environment';
import { Observable, throwError } from 'rxjs';
import { tap } from 'rxjs/operators';

const httpOptions = {
  headers: new HttpHeaders({ 'Content-Type': 'application/json' })
};

const ACCESS_TOKEN_KEY = 'agm_access_token';
const REFRESH_TOKEN_KEY = 'agm_refresh_token';

interface AuthResponse {
  success?: boolean;
  data?: {
    access_token?: string;
    refresh_token?: string;
    user?: {
      id?: number;
      email?: string;
      nombre?: string;
      rol?: string;
    };
  };
  access_token?: string;
  refresh_token?: string;
  access?: string;
  refresh?: string;
  token?: string;
  user?: {
    rol?: string;
    role?: string;
  };
  rol?: string;
  role?: string;
}

@Injectable({
  providedIn: 'root'
})
export class FacadeService {
  constructor(
    private http: HttpClient,
    public router: Router,

    private validatorService: ValidatorService,
    private errorService: ErrorsService,
  ) { }
  //Funcion para validar login
  public validarLogin(username: String, password: String){
    var data = {
      "username": username,
      "password": password
    }
    console.log("Validando login... ", data);
    let error: any = [];
    if(!this.validatorService.required(data["username"])){
      error["username"] = this.errorService.required;
    }else if(!this.validatorService.max(data["username"], 40)){
      error["username"] = this.errorService.max(40);
    }else if (!this.validatorService.email(data['username'])) {
      error['username'] = this.errorService.email;
    }
    if(!this.validatorService.required(data["password"])){
      error["password"] = this.errorService.required;
    }
    return error;
  }
  // Funciones básicas
  //Iniciar sesión
  public login(username: String, password: String): Observable<AuthResponse> {
    var data={
      email: username,
      password: password
    }
    return this.http.post<AuthResponse>(this.buildApiUrl('/auth/login'), data, httpOptions);
  }

  public storeTokens(response: AuthResponse, remember = false): string | null {
    const accessToken = this.extractAccessToken(response);
    const refreshToken = this.extractRefreshToken(response);

    if (!accessToken) {
      return null;
    }

    const primaryStorage = remember ? localStorage : sessionStorage;
    const secondaryStorage = remember ? sessionStorage : localStorage;

    primaryStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    secondaryStorage.removeItem(ACCESS_TOKEN_KEY);

    if (refreshToken) {
      primaryStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
      secondaryStorage.removeItem(REFRESH_TOKEN_KEY);
    }

    // Guardar también el rol del usuario para acceso rápido
    if (response?.data?.user?.rol) {
      primaryStorage.setItem('user_role', response.data.user.rol);
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
  }

  public isAuthenticated(): boolean {
    return Boolean(this.getAccessToken());
  }

  public getUserRole(): string | null {
    const payload = this.getJwtPayload(this.getAccessToken());

    // Intentar obtener del JWT primero
    const roleFromJwt = payload?.['rol'] ??
      payload?.['role'] ??
      payload?.['user']?.['rol'] ??
      payload?.['user']?.['role'];

    if (roleFromJwt) {
      return this.normalizeRole(roleFromJwt);
    }

    // Fallback a localStorage
    const storedRole = sessionStorage.getItem('user_role') || localStorage.getItem('user_role');
    return this.normalizeRole(storedRole);
  }

  public resolveHomeRoute(role: string | null): string {
    const normalizedRole = this.normalizeRole(role);

    if (normalizedRole === 'admin') {
      return '/admin/dashboard';
    }

    if (normalizedRole === 'docente') {
      return '/docente/dashboard';
    }

    if (normalizedRole === 'alumno') {
      return '/alumno/dashboard';
    }

    return '/login';
  }

  private buildApiUrl(path: string): string {
    const baseUrl = environment.apiBaseUrl || environment.url_api || '';

    return `${baseUrl.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
  }

  private extractAccessToken(response: AuthResponse): string | null {
    return response?.data?.access_token ?? response?.access_token ?? response?.access ?? response?.token ?? null;
  }

  private extractRefreshToken(response: AuthResponse): string | null {
    return response?.data?.refresh_token ?? response?.refresh_token ?? response?.refresh ?? null;
  }

  private getJwtPayload(token: string | null): Record<string, any> | null {
    if (!token) {
      return null;
    }

    const parts = token.split('.');

    if (parts.length < 2) {
      return null;
    }

    try {
      const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=');
      const decoded = atob(padded);

      return JSON.parse(decoded) as Record<string, any>;
    } catch {
      return null;
    }
  }

  private normalizeRole(role: string | null | undefined): string | null {
    if (!role) {
      return null;
    }

    return String(role).trim().toLowerCase();
  }
  
  public refreshToken(): Observable<any> {
    const refresh = this.getRefreshToken();

    if (!refresh) {
      return throwError(() => new Error('No refresh token'));
    }

    return this.http.post<any>(this.buildApiUrl('/auth/refresh'), { refresh }).pipe(
      tap((resp: any) => {
        const access = this.extractAccessToken(resp);
        const refreshTok = this.extractRefreshToken(resp);

        if (access) {
          const primaryStorage = sessionStorage;
          primaryStorage.setItem(ACCESS_TOKEN_KEY, access);
          localStorage.removeItem(ACCESS_TOKEN_KEY);
        }

        if (refreshTok) {
          sessionStorage.setItem(REFRESH_TOKEN_KEY, refreshTok);
          localStorage.removeItem(REFRESH_TOKEN_KEY);
        }
      })
    );
  }

  public logout(): void {
    // Optionally call backend logout endpoint here if needed
    this.clearSession();
    try {
      this.router.navigate(['/login']);
    } catch {
      // ignore navigation errors in non-routing contexts
    }
  }
  //Cerrar sesión
  // public logout(): Observable<any> {
  //   var headers: any;
  //   var token = this.getSessionToken();
  //   headers = new HttpHeaders({ 'Content-Type': 'application/json' , 'Authorization': 'Bearer '+token});
  //   return this.http.get<any>(`${environment.url_api}/logout/`, {headers: headers});
  // }
  // //Funciones para utilizar las cookies en web
  // retrieveSignedUser(){
  //   var headers: any;
  //   var token = this.getSessionToken();
  //   headers = new HttpHeaders({'Authorization': 'Bearer '+token});
  //   return this.http.get<any>(`${environment.url_api}/me/`,{headers:headers});
  // }

}