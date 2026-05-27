import { CommonModule } from '@angular/common';
import { Component, inject, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { AuthService } from '../../../services/auth.service';
import {
  DashboardClaseItem,
  DashboardDocenteService,
  DashboardResumenMateriaItem,
} from '../../../services/docente-services/dashboard-docente.service';

@Component({
  selector: 'app-dashboard-docente-screen',
  standalone: true,
  imports: [CommonModule, BottomNavbarDocente, TopbarAdmin, RouterLink],
  templateUrl: './dashboard-screen.html',
  styleUrl: './dashboard-screen.scss',
})
export class DashboardScreen implements OnInit {
  private readonly auth = inject(AuthService);

  nombreUsuario = '';
  rolLabel = '';
  fechaHoy = '';

  clasesHoy: DashboardClaseItem[] = [];
  resumenMaterias: DashboardResumenMateriaItem[] = [];

  totalMateriasAsignadas = 0;
  totalAlumnosInscritos = 0;
  periodoActivoNombre: string | null = null;
  emptyMessage = '';
  isLoading = true;
  loadError = '';

  ultimaActualizacion = '';

  constructor(private readonly dashboardService: DashboardDocenteService) {}

  ngOnInit(): void {
    this.fechaHoy = this.auth.formatTodayLong();
    this.auth.refreshCurrentUser().subscribe({
      next: (user) => {
        this.nombreUsuario = user?.nombre?.trim() || this.auth.getGreetingName();
        this.rolLabel = this.auth.getRoleLabel(user?.rol);
      },
      error: () => {
        this.nombreUsuario = this.auth.getGreetingName();
        this.rolLabel = this.auth.getRoleLabel();
      },
    });
    this.cargarDashboard();
  }

  private cargarDashboard(): void {
    this.isLoading = true;
    this.loadError = '';

    this.dashboardService
      .loadDashboard()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (data) => {
          this.periodoActivoNombre = data.periodoActivoNombre;
          this.clasesHoy = data.clasesHoy;
          this.resumenMaterias = data.resumenMaterias;
          this.totalMateriasAsignadas = data.totalMateriasAsignadas;
          this.totalAlumnosInscritos = data.totalAlumnosInscritos;
          this.emptyMessage = data.emptyMessage;
          this.ultimaActualizacion = new Date().toLocaleTimeString('es-MX', {
            hour: '2-digit',
            minute: '2-digit',
          });
        },
        error: () => {
          this.loadError = 'No se pudo cargar el resumen del docente.';
          this.clasesHoy = [];
          this.resumenMaterias = [];
        },
      });
  }
}
