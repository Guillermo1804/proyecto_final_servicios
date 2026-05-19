import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { RouterLink } from '@angular/router';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { FacadeService } from '../../../services/facade.service';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

interface PeriodoStat {
  materia_id?: number;
  materia_nombre?: string;
  periodo_nombre?: string;
  total_alumnos?: number;
  porcentaje_asistencia?: number;
  aprobados?: number;
  reprobados?: number;
}

@Component({
  selector: 'app-materias-docente-screen',
  standalone: true,
  imports: [CommonModule, BottomNavbarDocente, RouterLink, TopbarAdmin],
  templateUrl: './materias-screen.html',
  styleUrl: './materias-screen.scss',
})
export class MateriasScreen implements OnInit {
  materias: Array<{
    id: number;
    codigo: string;
    nombre: string;
    periodo: string;
    alumnos: number;
    progreso: number;
    horario: string;
  }> = [];
  loading = true;
  errorMessage = '';
  resumenSemanal = '';

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    const docenteId = this.facade.getUserId();
    if (!docenteId) {
      this.loading = false;
      this.errorMessage = 'Sesión inválida.';
      return;
    }
    forkJoin({
      materias: this.facade.listMateriasDocente(docenteId),
      stats: this.facade
        .getEstadisticasDocente(docenteId)
        .pipe(catchError(() => of({ success: false, data: null }))),
    }).subscribe({
      next: ({ materias, stats }) => {
        this.loading = false;
        const statMap = new Map<number, PeriodoStat>();
        const periodos =
          (stats?.data as { periodos?: PeriodoStat[] } | null)?.periodos ?? [];
        periodos.forEach((p) => {
          if (p.materia_id) {
            statMap.set(p.materia_id, p);
          }
        });

        const rows = this.facade.extractList<{
          id?: number;
          nrc?: string;
          nombre?: string;
          horario?: string;
        }>(materias);

        this.materias = rows.map((m) => {
          const sid = m.id ?? 0;
          const st = statMap.get(sid);
          const total = st?.total_alumnos ?? 0;
          const evaluados = (st?.aprobados ?? 0) + (st?.reprobados ?? 0);
          const progresoCalif =
            total > 0 ? Math.round((evaluados / total) * 100) : 0;
          const progresoAsist = Math.round(st?.porcentaje_asistencia ?? 0);
          return {
            id: sid,
            codigo: m.nrc ?? '—',
            nombre: m.nombre ?? '—',
            periodo: st?.periodo_nombre ?? '—',
            alumnos: total,
            progreso: progresoCalif || progresoAsist,
            horario: m.horario ?? '—',
          };
        });

        if (periodos.length) {
          const promAsist =
            periodos.reduce((acc, p) => acc + (p.porcentaje_asistencia ?? 0), 0) /
            periodos.length;
          this.resumenSemanal = `Asistencia promedio del periodo: ${Math.round(promAsist)}% en ${periodos.length} materia(s).`;
        } else {
          this.resumenSemanal = 'Sin estadísticas aún; inicia sesiones de asistencia y calificaciones.';
        }
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudieron cargar tus materias.';
      },
    });
  }
}
