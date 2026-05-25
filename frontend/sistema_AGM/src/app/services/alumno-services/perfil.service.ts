import { Injectable } from '@angular/core';
import { Observable, map, of, shareReplay, switchMap } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { AuthService } from '../auth.service';
import { AlumnosService } from './alumnos.service';

export interface Perfil {
  nombre: string;
  matricula: string;
  carrera?: string;
}

@Injectable({ providedIn: 'root' })
export class PerfilService {
  private profile$?: Observable<Perfil>;

  constructor(
    private auth: AuthService,
    private alumnos: AlumnosService,
  ) {}

  getProfile(forceRefresh = false): Observable<Perfil> {
    if (!this.profile$ || forceRefresh) {
      const fromToken = this.extractFromToken(this.auth.getAccessToken());
      if (fromToken && !forceRefresh) {
        this.profile$ = of(fromToken).pipe(shareReplay(1));
      } else {
        this.profile$ = this.auth.getMe().pipe(
          switchMap((response) => {
            const user = response.data;
            if (!user) {
              throw new Error('Sin datos de usuario');
            }
            if (this.auth.getUserRole() === 'alumno') {
              return this.alumnos.getMeMaterias(1, 1).pipe(
                map((page) => {
                  const inscripcion = page.results[0];
                  const alumno = inscripcion?.alumno;
                  if (alumno) {
                    return {
                      nombre: `${alumno.nombre} ${alumno.apellido}`.trim(),
                      matricula: alumno.matricula,
                      carrera: alumno.carrera,
                    };
                  }
                  return {
                    nombre: user.nombre,
                    matricula: user.email,
                    carrera: '',
                  };
                }),
              );
            }
            return of({
              nombre: user.nombre,
              matricula: user.email,
              carrera: '',
            });
          }),
          catchError(() =>
            of({
              nombre: 'Alumno',
              matricula: '—',
              carrera: '',
            } as Perfil),
          ),
          shareReplay(1),
        );
      }
    }

    return this.profile$;
  }

  private extractFromToken(token: string | null): Perfil | null {
    if (!token) {
      return null;
    }

    try {
      const parts = token.split('.');
      if (parts.length < 2) {
        return null;
      }

      const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=');
      const payload = JSON.parse(atob(padded)) as Record<string, unknown>;

      const nombre = String(
        payload['nombre'] ?? payload['name'] ?? (payload['user'] as Record<string, unknown>)?.['nombre'] ?? '',
      ).trim();
      const matricula = String(
        payload['matricula'] ??
          payload['matric'] ??
          (payload['user'] as Record<string, unknown>)?.['matricula'] ??
          '',
      ).trim();

      if (nombre && matricula) {
        return { nombre, matricula };
      }
    } catch {
      // ignore
    }

    return null;
  }
}
