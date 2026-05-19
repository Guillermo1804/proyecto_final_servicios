import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';
import { FacadeService } from '../../../services/facade.service';

@Component({
  selector: 'app-dashboard-screen',
  standalone: true,
  imports: [CommonModule, RouterLink, TopbarAdmin, BottomNavbarAlumno],
  templateUrl: './dashboard-screen.html',
  styleUrl: './dashboard-screen.scss',
})
export class DashboardScreen implements OnInit {
  nombreAlumno = 'Alumno';
  promedioGeneral = '—';
  materiasHoy: Array<{
    icono: string;
    color: string;
    materia: string;
    aula: string;
    horario: string;
  }> = [];
  evaluaciones: Array<{ materia: string; fecha: string; valor: string }> = [];
  materiasInscritas = 0;
  loading = true;
  errorMessage = '';

  private readonly colores = ['azul', 'naranja', 'morado', 'gris'];

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    forkJoin({
      me: this.facade.getMe(),
      inscripciones: this.facade.getMisMateriasAlumno(),
    }).subscribe({
      next: ({ me, inscripciones }) => {
        const rows = this.facade.extractList<{
          materia_detail?: {
            nombre?: string;
            nrc?: string;
            docente_nombre?: string;
            horario?: string;
          };
          alumno?: { id?: number; nombre?: string; apellido?: string };
        }>(inscripciones);

        const alumno = rows[0]?.alumno;
        const alumnoId = alumno?.id ?? 0;
        const nombreMs3 = [alumno?.nombre, alumno?.apellido].filter(Boolean).join(' ').trim();
        const user = me?.data;
        this.nombreAlumno = nombreMs3 || user?.nombre || 'Alumno';

        this.materiasInscritas = rows.length;
        this.materiasHoy = rows.slice(0, 5).map((row, idx) => ({
          icono: 'bi-book',
          color: this.colores[idx % this.colores.length],
          materia: row.materia_detail?.nombre ?? 'Materia',
          aula: row.materia_detail?.docente_nombre ?? '—',
          horario: row.materia_detail?.horario ?? '—',
        }));

        if (!alumnoId) {
          this.loading = false;
          return;
        }

        this.facade
          .getEstadisticasAlumno(alumnoId)
          .pipe(catchError(() => of({ success: false, data: null })))
          .subscribe({
            next: (stats) => {
              this.loading = false;
              const materias =
                (stats?.data as {
                  materias?: Array<{
                    materia_nombre?: string;
                    promedio_redondeado?: number;
                    promedio_real?: string;
                    porcentaje_asistencia?: number;
                  }>;
                } | null)?.materias ?? [];

              const proms = materias
                .map((m) => m.promedio_redondeado ?? parseFloat(m.promedio_real ?? ''))
                .filter((n) => !Number.isNaN(n));
              if (proms.length) {
                this.promedioGeneral = (
                  proms.reduce((a, b) => a + b, 0) / proms.length
                ).toFixed(1);
              }

              this.evaluaciones = materias.slice(0, 5).map((m) => ({
                materia: m.materia_nombre ?? '—',
                fecha: 'Corte actual',
                valor:
                  m.porcentaje_asistencia != null
                    ? `${m.porcentaje_asistencia}% asist.`
                    : String(m.promedio_redondeado ?? '—'),
              }));
            },
            error: () => {
              this.loading = false;
            },
          });
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudo cargar tu dashboard.';
      },
    });
  }
}
