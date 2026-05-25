import { CommonModule } from '@angular/common';
import { Component, inject, OnInit } from '@angular/core';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { AuthService } from '../../../services/auth.service';
import {
  DashboardDocenteService,
  DashboardClaseItem,
  DashboardNotificacionItem,
  DashboardPendienteItem,
  DashboardResumenMateriaItem,
} from '../../../services/docente-services/dashboard-docente.service';

@Component({
  selector: 'app-dashboard-docente-screen',
  standalone: true,
  imports: [CommonModule, BottomNavbarDocente, TopbarAdmin],
  templateUrl: './dashboard-screen.html',
  styleUrl: './dashboard-screen.scss'
})
export class DashboardScreen implements OnInit {
  private readonly auth = inject(AuthService);

  nombreUsuario = '';
  rolLabel = '';
  fechaHoy = '';

  clasesHoy: DashboardClaseItem[] = [];
  pendientes: DashboardPendienteItem[] = [];
  notificaciones: DashboardNotificacionItem[] = [];
  resumenMaterias: DashboardResumenMateriaItem[] = [];

  totalMateriasAsignadas = 0;
  totalAlumnosInscritos = 0;
  porcentajeAsistenciaDelDia = 0;
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
    this.clasesHoy = this.dashboardService.getClasesHoy();
    this.pendientes = this.dashboardService.getPendientes();
    this.notificaciones = this.dashboardService.getNotificaciones();
    this.resumenMaterias = this.dashboardService.getResumenMaterias();
    this.totalMateriasAsignadas = this.dashboardService.getTotalMateriasAsignadas();
    this.totalAlumnosInscritos = this.dashboardService.getTotalAlumnosInscritos();
    this.porcentajeAsistenciaDelDia = this.dashboardService.getPorcentajeAsistenciaDelDia();
    this.ultimaActualizacion = new Date().toLocaleTimeString('es-MX', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }

}