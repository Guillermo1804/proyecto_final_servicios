import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { FacadeService } from '../../../services/facade.service';

@Component({
  selector: 'app-dashboard-docente-screen',
  standalone: true,
  imports: [CommonModule, RouterLink, BottomNavbarDocente, TopbarAdmin],
  templateUrl: './dashboard-screen.html',
  styleUrl: './dashboard-screen.scss',
})
export class DashboardScreen implements OnInit {
  nombreDocente = 'Docente';
  materias: Array<{
    id: number;
    hora: string;
    materia: string;
    grupo: string;
    aula: string;
    icono: string;
    activo: boolean;
  }> = [];
  resumenStats: Array<{ label: string; valor: string }> = [];
  loading = true;
  errorMessage = '';

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    const uid = this.facade.getUserId();
    if (!uid) {
      this.loading = false;
      this.errorMessage = 'Sesión inválida.';
      return;
    }

    forkJoin({
      me: this.facade.getMe(),
      materias: this.facade.listMateriasDocente(uid),
      stats: this.facade.getEstadisticasDocente(uid).pipe(
        catchError(() => of({ success: false, data: null })),
      ),
    }).subscribe({
      next: ({ me, materias, stats }) => {
        this.loading = false;
        const user = me?.data;
        if (user?.nombre) {
          this.nombreDocente = user.nombre;
        }

        const rows = this.facade.extractList<{
          id?: number;
          nombre?: string;
          nrc?: string;
          seccion?: string;
          horario?: string;
        }>(materias);

        this.materias = rows.slice(0, 6).map((m, idx) => ({
          id: m.id ?? 0,
          hora: m.horario || '—',
          materia: m.nombre ?? '—',
          grupo: `NRC ${m.nrc ?? '—'} · Sec. ${m.seccion ?? '—'}`,
          aula: m.horario || 'Consultar horario',
          icono: idx === 0 ? 'bi-broadcast' : 'bi-people',
          activo: idx === 0,
        }));

        const periodos = (stats?.data as { periodos?: Array<{
          total_alumnos?: number;
          promedio_grupal?: number;
          porcentaje_asistencia?: number;
        }> } | null)?.periodos ?? [];

        const totalAlumnos = periodos.reduce((acc, p) => acc + (p.total_alumnos ?? 0), 0);
        const promedios = periodos
          .map((p) => parseFloat(String(p.promedio_grupal ?? '')))
          .filter((n) => !Number.isNaN(n));
        const asistencias = periodos
          .map((p) => parseFloat(String(p.porcentaje_asistencia ?? '')))
          .filter((n) => !Number.isNaN(n));

        const promGrupo =
          promedios.length > 0
            ? (promedios.reduce((a, b) => a + b, 0) / promedios.length).toFixed(1)
            : '—';
        const promAsist =
          asistencias.length > 0
            ? (asistencias.reduce((a, b) => a + b, 0) / asistencias.length).toFixed(0) + '%'
            : '—';

        this.resumenStats = [
          { label: 'Materias asignadas', valor: String(rows.length) },
          { label: 'Alumnos (total)', valor: String(totalAlumnos) },
          { label: 'Promedio grupal', valor: promGrupo },
          { label: 'Asistencia promedio', valor: promAsist },
        ];
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudo cargar el dashboard.';
      },
    });
  }
}
