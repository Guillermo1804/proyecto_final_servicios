import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';
import { DashboardService, AlumnoResumen, MateriaActual, MateriaHoy, EvaluacionItem } from '../../../services/alumno-services/dashboard.service';

@Component({
  selector: 'app-dashboard-screen',
  standalone: true,
  imports: [
    CommonModule,
    TopbarAdmin,
    BottomNavbarAlumno
  ],
  templateUrl: './dashboard-screen.html',
  styleUrl: './dashboard-screen.scss'
})
export class DashboardScreen implements OnInit {

  alumno: AlumnoResumen = { nombre: '', matricula: '' } as AlumnoResumen;
  materiasActuales: MateriaActual[] = [];
  materiasHoy: MateriaHoy[] = [];
  evaluaciones: EvaluacionItem[] = [];

  constructor(private dashboardService: DashboardService) {}

  ngOnInit(): void {
    this.alumno = this.dashboardService.getAlumno();
    this.materiasActuales = this.dashboardService.getMateriasActuales();
    this.materiasHoy = this.dashboardService.getMateriasHoy();
    this.evaluaciones = this.dashboardService.getEvaluaciones();
  }

}