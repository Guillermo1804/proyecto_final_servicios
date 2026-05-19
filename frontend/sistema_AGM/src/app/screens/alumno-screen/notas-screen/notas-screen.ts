import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';
import { FacadeService } from '../../../services/facade.service';

@Component({
  selector: 'app-notas-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarAlumno],
  templateUrl: './notas-screen.html',
  styleUrl: './notas-screen.scss',
})
export class NotasScreen implements OnInit {
  materias: Array<{
    materiaId: number;
    icono: string;
    color: string;
    nombre: string;
    nrc: string;
    profesor: string;
    promedio: number | string;
    promedioColor: string;
    expandido: boolean;
    parciales: Array<{ titulo: string; valor: string; activo?: boolean }>;
  }> = [];
  historial: Array<{ periodo: string; materias: number; aprobadas: number }> = [];
  loading = true;
  errorMessage = '';
  alumnoId = 0;
  bajaMateriaId: number | null = null;

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    this.facade.getMisMateriasAlumno().subscribe({
      next: (body) => {
        this.loading = false;
        const rows = this.facade.extractList<{
          materia_id?: number;
          alumno?: { id?: number };
          materia_detail?: { nombre?: string; nrc?: string; docente_nombre?: string };
        }>(body);
        if (rows[0]?.alumno?.id) {
          this.alumnoId = rows[0].alumno.id;
        }
        this.materias = rows.map((row, idx) => ({
          materiaId: row.materia_id ?? 0,
          icono: 'bi-book',
          color: ['azul', 'naranja', 'morado', 'gris'][idx % 4],
          nombre: row.materia_detail?.nombre ?? `Materia ${row.materia_id}`,
          nrc: row.materia_detail?.nrc ?? '—',
          profesor: row.materia_detail?.docente_nombre ?? '—',
          promedio: '—',
          promedioColor: 'gris',
          expandido: idx === 0,
          parciales: [],
        }));
        const first = this.materias.find((m) => m.expandido && m.materiaId);
        if (first) {
          this.cargarCalificacionesMateria(first);
        }
        if (this.alumnoId) {
          this.cargarHistorial();
        }
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudieron cargar tus materias.';
      },
    });
  }

  toggleMateria(materia: (typeof this.materias)[0]): void {
    materia.expandido = !materia.expandido;
    if (materia.expandido && materia.materiaId) {
      this.cargarCalificacionesMateria(materia);
    }
  }

  private cargarCalificacionesMateria(materia: (typeof this.materias)[0]): void {
    if (!materia.materiaId) {
      return;
    }
    this.facade.getConcentrado(materia.materiaId).subscribe({
      next: (body) => {
        const data = body?.data as {
          alumnos?: {
            alumno_id?: number;
            promedio_real?: string;
            promedio_redondeado?: number;
            calificaciones?: { actividad_id?: number; calificacion?: string; actividad_nombre?: string }[];
          }[];
          categorias?: {
            actividades?: { id?: number; nombre?: string }[];
          }[];
        };
        const alumnoRow =
          (data?.alumnos ?? []).find((a) => a.alumno_id === this.alumnoId) ??
          (data?.alumnos ?? [])[0];
        if (alumnoRow) {
          const red = alumnoRow.promedio_redondeado ?? 0;
          materia.promedio = alumnoRow.promedio_real ?? red;
          materia.promedioColor = red >= 6 ? 'verde' : 'rojo';
          materia.parciales = (alumnoRow.calificaciones ?? []).map((c) => ({
            titulo: c.actividad_nombre ?? `Actividad ${c.actividad_id}`,
            valor: c.calificacion ?? '—',
          }));
          if (!materia.parciales.length) {
            (data?.categorias ?? []).forEach((cat) => {
              (cat.actividades ?? []).forEach((act) => {
                materia.parciales.push({
                  titulo: act.nombre ?? `Actividad ${act.id}`,
                  valor: '—',
                });
              });
            });
          }
        }
      },
      error: () => {
        materia.parciales = [{ titulo: 'Sin calificaciones', valor: '—' }];
      },
    });
  }

  private cargarHistorial(): void {
    this.facade.getEstadisticasAlumno(this.alumnoId).subscribe({
      next: (body) => {
        const materias =
          (body?.data as {
            materias?: Array<{
              periodo_nombre?: string;
              promedio_redondeado?: number;
            }>;
          } | null)?.materias ?? [];
        const byPeriodo = new Map<string, { materias: number; aprobadas: number }>();
        materias.forEach((m) => {
          const periodo = m.periodo_nombre?.trim() || 'Sin periodo';
          const cur = byPeriodo.get(periodo) ?? { materias: 0, aprobadas: 0 };
          cur.materias += 1;
          if ((m.promedio_redondeado ?? 0) >= 6) {
            cur.aprobadas += 1;
          }
          byPeriodo.set(periodo, cur);
        });
        this.historial = Array.from(byPeriodo.entries()).map(([periodo, stats]) => ({
          periodo,
          materias: stats.materias,
          aprobadas: stats.aprobadas,
        }));
      },
      error: () => {
        this.historial = [];
      },
    });
  }

  confirmarBaja(materiaId: number): void {
    if (!this.alumnoId) {
      alert('No se encontró tu registro de alumno.');
      return;
    }
    if (
      !confirm(
        'La baja de materia es irreversible. ¿Deseas continuar?',
      )
    ) {
      return;
    }
    this.facade.bajaMateriaAlumno(this.alumnoId, materiaId).subscribe({
      next: () => {
        this.materias = this.materias.filter((m) => m.materiaId !== materiaId);
        alert('Baja procesada correctamente.');
      },
      error: (err) => {
        alert(err?.error?.message ?? 'No se pudo procesar la baja.');
      },
    });
  }
}
