import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';
import { FacadeService } from '../../../services/facade.service';

@Component({
  selector: 'app-perfil-screen',
  standalone: true,
  imports: [CommonModule, RouterLink, TopbarAdmin, BottomNavbarAlumno],
  templateUrl: './perfil-screen.html',
  styleUrl: './perfil-screen.scss',
})
export class PerfilScreen implements OnInit {
  loading = true;
  errorMessage = '';
  nombreCompleto = '—';
  email = '—';
  iniciales = '?';
  carrera = '—';
  matricula = '—';
  semestreLabel = '—';
  periodoNombre = '—';
  materiasActivas = 0;
  estatus = '—';
  activo = true;

  constructor(
    private facade: FacadeService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    forkJoin({
      me: this.facade.getMe(),
      materias: this.facade.getMisMateriasAlumno().pipe(
        catchError(() => of({ success: false, data: { results: [] } })),
      ),
      periodo: this.facade.getPeriodoActivo().pipe(
        catchError(() => of({ success: false, data: null })),
      ),
    }).subscribe({
      next: ({ me, materias, periodo }) => {
        this.loading = false;
        const user = me?.data;
        if (!user) {
          this.errorMessage = 'No se pudo cargar tu perfil.';
          return;
        }
        this.email = user.email ?? '—';
        this.nombreCompleto = user.nombre ?? '—';
        this.iniciales = this.buildIniciales(this.nombreCompleto);
        this.activo = user.activo !== false;
        this.estatus = this.activo ? 'Regular' : 'Inactivo';

        const p = periodo?.data as { nombre?: string } | null | undefined;
        if (p?.nombre) {
          this.periodoNombre = p.nombre;
        }

        const rows = this.facade.extractList<{
          alumno?: {
            matricula?: string;
            nombre?: string;
            apellido?: string;
            carrera?: string;
            semestre?: number;
            activo?: boolean;
          };
        }>(materias);
        this.materiasActivas = rows.length;
        const alumno = rows[0]?.alumno;
        if (alumno) {
          const nombre = [alumno.nombre, alumno.apellido].filter(Boolean).join(' ').trim();
          if (nombre) {
            this.nombreCompleto = nombre;
            this.iniciales = this.buildIniciales(nombre);
          }
          this.matricula = alumno.matricula ?? '—';
          this.carrera = alumno.carrera || '—';
          if (alumno.semestre != null) {
            this.semestreLabel = `${alumno.semestre}° semestre`;
          }
          if (alumno.activo === false) {
            this.estatus = 'Inactivo';
            this.activo = false;
          }
        }
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudo cargar tu perfil.';
      },
    });
  }

  logout(): void {
    this.facade.logout().subscribe({
      next: () => this.router.navigate(['/login'], { replaceUrl: true }),
      error: () => {
        this.facade.clearSession();
        this.router.navigate(['/login'], { replaceUrl: true });
      },
    });
  }

  private buildIniciales(nombre: string): string {
    const parts = nombre.trim().split(/\s+/).filter(Boolean);
    if (!parts.length) {
      return '?';
    }
    if (parts.length === 1) {
      return parts[0].slice(0, 2).toUpperCase();
    }
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
}
