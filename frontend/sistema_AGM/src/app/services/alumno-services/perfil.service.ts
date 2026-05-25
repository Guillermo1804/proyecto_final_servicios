import { Injectable } from '@angular/core';
import { Observable, map, of, shareReplay, switchMap } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { AlumnoApiDto } from '../../models/alumnos-api.model';
import { AuthService } from '../auth.service';
import { AlumnosService } from './alumnos.service';

export interface Perfil {
  nombre: string;
  matricula: string;
  carrera?: string;
  email?: string;
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
      if (this.auth.getUserRole() === 'alumno') {
        this.profile$ = this.alumnos.getMe().pipe(
          map((alumno) => this.mapAlumnoPerfil(alumno)),
          catchError(() => this.fallbackPerfil()),
          shareReplay(1),
        );
      } else {
        this.profile$ = this.auth.getMe().pipe(
          map((response) => {
            const user = response.data;
            return {
              nombre: user?.nombre?.trim() || 'Usuario',
              matricula: user?.email || '—',
              carrera: '',
              email: user?.email,
            };
          }),
          catchError(() => this.fallbackPerfil()),
          shareReplay(1),
        );
      }
    }

    return this.profile$;
  }

  private mapAlumnoPerfil(alumno: AlumnoApiDto): Perfil {
    const nombre = AlumnosService.mapAlumnoNombre(alumno);
    return {
      nombre,
      matricula: alumno.matricula,
      carrera: alumno.carrera,
      email: alumno.email,
    };
  }

  private fallbackPerfil(): Observable<Perfil> {
    const stored = this.auth.getStoredUser();
    return of({
      nombre: stored?.nombre?.trim() || 'Usuario',
      matricula: stored?.email || '—',
      carrera: '',
      email: stored?.email,
    });
  }
}
