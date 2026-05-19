import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { TopbarAdmin } from '../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAdmin } from '../../partials/bottom-navbar-admin/bottom-navbar-admin';
import { FacadeService } from '../../services/facade.service';

interface StatCard {
  icono: string;
  titulo: string;
  valor: string;
  estado: string;
  tipo: string;
  color: string;
}

@Component({
  selector: 'app-dashboard-screen',
  standalone: true,
  imports: [CommonModule, RouterLink, TopbarAdmin, BottomNavbarAdmin],
  templateUrl: './dashboard-screen.html',
  styleUrl: './dashboard-screen.scss',
})
export class DashboardScreen implements OnInit {
  estadisticas: StatCard[] = [];
  periodoActivoNombre = '—';
  loading = true;
  errorMessage = '';

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    forkJoin({
      periodos: this.facade.listPeriodos(1, 1),
      periodoActivo: this.facade.getPeriodoActivo(),
      materias: this.facade.listMaterias({ page: 1, limit: 1 }),
      docentes: this.facade.listDocentes({ page: 1, limit: 1 }),
      alumnos: this.facade.listAlumnos({ page: 1, limit: 1 }),
    }).subscribe({
      next: ({ periodos, periodoActivo, materias, docentes, alumnos }) => {
        this.loading = false;
        const activo = periodoActivo?.data as { nombre?: string; activo?: boolean } | undefined;
        if (activo?.nombre) {
          this.periodoActivoNombre = activo.nombre;
        }

        const totalPeriodos = this.facade.extractCount(periodos);
        const totalMaterias = this.facade.extractCount(materias);
        const totalDocentes = this.facade.extractCount(docentes);
        const totalAlumnos = this.facade.extractCount(alumnos);

        this.estadisticas = [
          {
            icono: 'bi-people',
            titulo: 'TOTAL DE ALUMNOS',
            valor: String(totalAlumnos),
            estado: 'MS-3',
            tipo: 'verde',
            color: 'azul',
          },
          {
            icono: 'bi-mortarboard',
            titulo: 'TOTAL DE DOCENTES',
            valor: String(totalDocentes),
            estado: 'MS-3',
            tipo: 'gris',
            color: 'azul',
          },
          {
            icono: 'bi-journal-bookmark',
            titulo: 'MATERIAS REGISTRADAS',
            valor: String(totalMaterias),
            estado: 'MS-2',
            tipo: 'verde',
            color: 'naranja',
          },
          {
            icono: 'bi-calendar',
            titulo: 'PERIODOS REGISTRADOS',
            valor: String(totalPeriodos),
            estado: activo?.activo ? 'Activo' : '—',
            tipo: activo?.activo ? 'verde' : 'gris',
            color: 'gris',
          },
        ];
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudieron cargar las estadísticas del sistema.';
      },
    });
  }
}
