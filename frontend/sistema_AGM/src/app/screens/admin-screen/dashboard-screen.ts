import { CommonModule } from '@angular/common';
import { Component, inject, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { TopbarAdmin } from '../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAdmin } from '../../partials/bottom-navbar-admin/bottom-navbar-admin';
import { AuthService } from '../../services/auth.service';
import {
  AdminDashboardResumen,
  DashboardService,
} from '../../services/admin-services/dashboard.service';

@Component({
  selector: 'app-dashboard-screen',
  standalone: true,
  imports: [CommonModule, RouterLink, TopbarAdmin, BottomNavbarAdmin],
  templateUrl: './dashboard-screen.html',
  styleUrl: './dashboard-screen.scss',
})
export class DashboardScreen implements OnInit {
  private readonly dashboardService = inject(DashboardService);
  private readonly auth = inject(AuthService);

  nombreUsuario = '';
  rolLabel = '';
  fechaHoy = '';

  readonly acciones = this.dashboardService.getAcciones();

  resumen: AdminDashboardResumen | null = null;
  isLoadingResumen = true;
  resumenError = '';

  ngOnInit(): void {
    this.fechaHoy = this.auth.formatTodayLong();
    this.loadUsuario();
    this.loadResumen();
  }

  formatFecha(fecha: string): string {
    if (!fecha?.trim()) {
      return '—';
    }
    const parsed = new Date(`${fecha}T12:00:00`);
    if (Number.isNaN(parsed.getTime())) {
      return fecha;
    }
    return parsed.toLocaleDateString('es-MX', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  }

  private loadUsuario(): void {
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
  }

  private loadResumen(): void {
    this.isLoadingResumen = true;
    this.resumenError = '';

    this.dashboardService
      .loadResumen()
      .pipe(finalize(() => {
        this.isLoadingResumen = false;
      }))
      .subscribe({
        next: (resumen) => {
          this.resumen = resumen;
        },
        error: () => {
          this.resumenError = 'No se pudo cargar el resumen del sistema.';
          this.resumen = {
            totalPeriodos: 0,
            periodoActivo: null,
            materiasPeriodoActivo: 0,
            totalDocentes: 0,
          };
        },
      });
  }
}
