import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TopbarAdmin } from "../../partials/topbar-admin/topbar-admin";
import { BottomNavbarAdmin } from "../../partials/bottom-navbar-admin/bottom-navbar-admin";
import { DashboardService } from '../../services/admin-services/dashboard.service';

@Component({
  selector: 'app-dashboard-screen',
  standalone: true,
  imports: [CommonModule, RouterLink, TopbarAdmin, BottomNavbarAdmin],
  templateUrl: './dashboard-screen.html',
  styleUrl: './dashboard-screen.scss'
})
export class DashboardScreen {

  private readonly dashboardService = inject(DashboardService);

  readonly estadisticas = this.dashboardService.getEstadisticas();
  readonly actividades = this.dashboardService.getActividades();
  readonly acciones = this.dashboardService.getAcciones();

}