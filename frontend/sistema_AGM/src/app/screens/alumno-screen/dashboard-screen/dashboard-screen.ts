import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';
import { AuthService } from '../../../services/auth.service';
import { AlumnosService } from '../../../services/alumno-services/alumnos.service';
import { PerfilService } from '../../../services/alumno-services/perfil.service';
import {
  AlumnoResumen,
  DashboardService,
  EvaluacionDetalle,
  MateriaActual,
  MateriaHoy,
} from '../../../services/alumno-services/dashboard.service';

@Component({
  selector: 'app-dashboard-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarAlumno, RouterLink],
  templateUrl: './dashboard-screen.html',
  styleUrl: './dashboard-screen.scss',
})
export class DashboardScreen implements OnInit {
  alumno: AlumnoResumen = { nombre: '', matricula: '', tipoFormacion: '—', periodoActivo: '—' };
  rolLabel = '';
  emailUsuario = '';
  materiasActuales: MateriaActual[] = [];
  materiasHoy: MateriaHoy[] = [];
  evaluaciones: EvaluacionDetalle[] = [];
  perfilLoading = true;
  materiasLoading = true;
  materiasError = '';
  fechaHoyLabel = '';

  materiaExpandidaId: number | null = null;
  claseHoyExpandidaId: number | null = null;
  evaluacionExpandidaId: number | null = null;

  constructor(
    private auth: AuthService,
    private perfilService: PerfilService,
    private dashboardService: DashboardService,
  ) {}

  ngOnInit(): void {
    this.rolLabel = this.auth.getRoleLabel();
    this.fechaHoyLabel = this.dashboardService.getFechaHoyLabel();

    this.auth.refreshCurrentUser().subscribe({
      next: (user) => {
        this.emailUsuario = user?.email || '';
      },
    });

    this.perfilService.getProfile(true).subscribe({
      next: (perfil) => {
        this.alumno = {
          nombre: perfil.nombre,
          matricula: perfil.matricula,
          tipoFormacion: perfil.carrera || '—',
          periodoActivo: '—',
        };
        if (perfil.email) {
          this.emailUsuario = perfil.email;
        }
        this.perfilLoading = false;
      },
      error: () => {
        const user = this.auth.getStoredUser();
        this.alumno = {
          nombre: user?.nombre || 'Usuario',
          matricula: user?.email || '—',
          tipoFormacion: '—',
          periodoActivo: '—',
        };
        this.perfilLoading = false;
      },
    });

    this.dashboardService
      .loadDashboard()
      .pipe(finalize(() => (this.materiasLoading = false)))
      .subscribe({
        next: (data) => {
          this.materiasActuales = data.materiasActuales;
          this.materiasHoy = data.materiasHoy;
          this.evaluaciones = data.evaluaciones;
          this.alumno = {
            ...this.alumno,
            periodoActivo: data.periodoActivo,
          };
          this.materiasError = '';
        },
        error: (err) => {
          this.materiasError = AlumnosService.extractError(
            err,
            'No se pudieron cargar tus materias inscritas (MS-3).',
          );
          this.materiasActuales = [];
          this.materiasHoy = [];
          this.evaluaciones = [];
        },
      });
  }

  toggleMateria(materiaId: number): void {
    this.materiaExpandidaId = this.materiaExpandidaId === materiaId ? null : materiaId;
  }

  toggleClaseHoy(materiaId: number): void {
    this.claseHoyExpandidaId = this.claseHoyExpandidaId === materiaId ? null : materiaId;
  }

  toggleEvaluacion(actividadId: number): void {
    this.evaluacionExpandidaId = this.evaluacionExpandidaId === actividadId ? null : actividadId;
  }

  esMateriaExpandida(materiaId: number): boolean {
    return this.materiaExpandidaId === materiaId;
  }

  esClaseHoyExpandida(materiaId: number): boolean {
    return this.claseHoyExpandidaId === materiaId;
  }

  esEvaluacionExpandida(actividadId: number): boolean {
    return this.evaluacionExpandidaId === actividadId;
  }
}
