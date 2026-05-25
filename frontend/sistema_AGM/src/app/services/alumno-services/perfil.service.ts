import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError, shareReplay } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { FacadeService } from '../facade.service';

export interface Perfil {
  nombre: string;
  matricula: string;
  carrera?: string;
}

@Injectable({
  providedIn: 'root'
})
export class PerfilService {
  private profile$?: Observable<Perfil>;

  constructor(private http: HttpClient, private facade: FacadeService) {}

  getProfile(forceRefresh = false): Observable<Perfil> {
    if (!this.profile$ || forceRefresh) {
      const token = this.facade.getAccessToken();
      const fromToken = this.extractFromToken(token);

      if (fromToken) {
        this.profile$ = of(fromToken).pipe(shareReplay(1));
      } else {
        const base = (environment.apiBaseUrl || (environment as any).url_api || '').replace(/\/$/, '');
        this.profile$ = this.http
          .get<Perfil>(`${base}/alumnos/me`)
          .pipe(
            catchError((err) => {
              console.warn('PerfilService: no se pudo contactar backend /alumnos/me, usando mock:', err);
              const mock: Perfil = { nombre: 'Alumno de Prueba', matricula: '20210001' };
              return of(mock);
            }),
            shareReplay(1)
          );
      }
    }

    return this.profile$;
  }

  private extractFromToken(token: string | null): Perfil | null {
    if (!token) return null;

    try {
      const parts = token.split('.');
      if (parts.length < 2) return null;

      const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=');
      const decoded = atob(padded);
      const payload = JSON.parse(decoded) as any;

      const nombre = payload?.nombre || payload?.name || payload?.user?.nombre || payload?.user?.name;
      const matricula = payload?.matricula || payload?.matric || payload?.user?.matricula || payload?.user?.matric;

      if (nombre && matricula) {
        return { nombre, matricula } as Perfil;
      }
    } catch {
      // ignore
    }

    return null;
  }
}
