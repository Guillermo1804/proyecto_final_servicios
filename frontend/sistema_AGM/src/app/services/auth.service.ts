import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';

export interface AuthResponse {
  success: boolean;
  data: {
    access_token: string;
    refresh_token: string;
    user: {
      id: number;
      email: string;
      nombre: string;
      rol: 'admin' | 'docente' | 'alumno';
    };
  };
  message: string;
}

export interface User {
  id: number;
  email: string;
  nombre: string;
  rol: 'admin' | 'docente' | 'alumno';
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  /** @deprecated Usar FacadeService (gateway :8080). Se mantiene por compatibilidad. */
  private apiUrl = 'http://localhost:8080/auth';
  private currentUser = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUser.asObservable();

  constructor(private http: HttpClient) {
    this.loadUserFromStorage();
  }

  login(email: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, {
      email,
      password
    }).pipe(
      tap((response: AuthResponse) => {
        if (response.success && response.data) {
          localStorage.setItem('access_token', response.data.access_token);
          localStorage.setItem('refresh_token', response.data.refresh_token);
          localStorage.setItem('user', JSON.stringify(response.data.user));
          this.currentUser.next(response.data.user);
        }
      })
    );
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    this.currentUser.next(null);
  }

  getCurrentUser(): User | null {
    return this.currentUser.value;
  }

  getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  private loadUserFromStorage(): void {
    const userJson = localStorage.getItem('user');
    if (userJson) {
      try {
        this.currentUser.next(JSON.parse(userJson));
      } catch (e) {
        console.error('Error loading user from storage:', e);
      }
    }
  }
}
