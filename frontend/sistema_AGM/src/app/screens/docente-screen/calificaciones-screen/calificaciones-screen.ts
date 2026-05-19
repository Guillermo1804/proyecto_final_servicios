import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { FacadeService } from '../../../services/facade.service';

interface ColumnaActividad {
  actividadId: number;
  label: string;
  porcentajeCategoria: string;
}

interface EstudianteRow {
  alumnoId: number;
  nombre: string;
  id: string;
  notas: Record<number, string>;
  promedioReal: string;
  promedioRedondeado: number;
  riesgo: boolean;
}

interface MateriaOption {
  id: number;
  label: string;
}

@Component({
  selector: 'app-calificaciones-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './calificaciones-screen.html',
  styleUrl: './calificaciones-screen.scss',
})
export class CalificacionesScreen implements OnInit {
  materias: MateriaOption[] = [];
  selectedMateriaId = 0;
  columnas: ColumnaActividad[] = [];
  estudiantes: EstudianteRow[] = [];
  loading = true;
  saving = false;
  errorMessage = '';
  successMessage = '';

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    const uid = this.facade.getUserId();
    this.facade.listMaterias({ limit: 100 }).subscribe({
      next: (body) => {
        const rows = this.facade.extractList<{
          id?: number;
          nombre?: string;
          nrc?: string;
          docente_id?: number;
        }>(body);
        const filtered = uid
          ? rows.filter((m) => m.docente_id === uid)
          : rows;
        this.materias = filtered
          .filter((m) => m.id)
          .map((m) => ({
            id: m.id as number,
            label: `${m.nrc ?? ''} ${m.nombre ?? ''}`.trim(),
          }));
        if (this.materias.length) {
          this.selectedMateriaId = this.materias[0].id;
          this.loadConcentrado();
        } else {
          this.loading = false;
        }
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudieron cargar las materias.';
      },
    });
  }

  onMateriaChange(): void {
    this.loadConcentrado();
  }

  loadConcentrado(): void {
    if (!this.selectedMateriaId) {
      return;
    }
    this.loading = true;
    this.errorMessage = '';
    this.facade.getConcentrado(this.selectedMateriaId).subscribe({
      next: (body) => {
        this.loading = false;
        const data = body?.data as {
          categorias?: {
            nombre?: string;
            porcentaje?: string;
            actividades?: { id?: number; nombre?: string }[];
          }[];
          alumnos?: {
            alumno_id?: number;
            matricula?: string;
            nombre?: string;
            calificaciones?: { actividad_id?: number; calificacion?: string }[];
            promedio_real?: string;
            promedio_redondeado?: number;
          }[];
        };
        this.columnas = [];
        (data?.categorias ?? []).forEach((cat) => {
          (cat.actividades ?? []).forEach((act) => {
            if (act.id) {
              this.columnas.push({
                actividadId: act.id,
                label: act.nombre ?? `Actividad ${act.id}`,
                porcentajeCategoria: cat.porcentaje ?? '',
              });
            }
          });
        });
        this.estudiantes = (data?.alumnos ?? []).map((a) => {
          const notas: Record<number, string> = {};
          (a.calificaciones ?? []).forEach((c) => {
            if (c.actividad_id != null) {
              notas[c.actividad_id] = c.calificacion ?? '';
            }
          });
          const red = a.promedio_redondeado ?? 0;
          return {
            alumnoId: a.alumno_id ?? 0,
            nombre: a.nombre ?? '—',
            id: a.matricula ?? String(a.alumno_id ?? ''),
            notas,
            promedioReal: a.promedio_real ?? '0.00',
            promedioRedondeado: red,
            riesgo: red < 6,
          };
        });
      },
      error: () => {
        this.loading = false;
        this.errorMessage =
          'No hay concentrado para esta materia (configure ponderaciones y actividades).';
        this.estudiantes = [];
        this.columnas = [];
      },
    });
  }

  calcularPromedioRedondeado(promedio: number): number {
    const entero = Math.floor(promedio);
    const decimal = promedio - entero;
    return decimal >= 0.5 ? entero + 1 : entero;
  }

  onNotaBlur(estudiante: EstudianteRow, actividadId: number): void {
    const valor = estudiante.notas[actividadId];
    if (!valor || !estudiante.alumnoId) {
      return;
    }
    this.saving = true;
    this.facade
      .upsertCalificacion({
        actividad_id: actividadId,
        alumno_id: estudiante.alumnoId,
        calificacion: valor,
      })
      .subscribe({
        next: () => {
          this.saving = false;
          this.loadConcentrado();
        },
        error: () => {
          this.saving = false;
          this.errorMessage = 'No se pudo guardar la calificación.';
        },
      });
  }

  publicarNotas(): void {
    if (!this.selectedMateriaId) {
      return;
    }
    this.saving = true;
    this.facade.imprimirListaCalificaciones(this.selectedMateriaId).subscribe({
      next: () => {
        this.saving = false;
        this.successMessage = 'Lista marcada como impresa; edición bloqueada.';
      },
      error: () => {
        this.saving = false;
        this.errorMessage = 'No se pudo publicar la lista.';
      },
    });
  }

  get promedioGeneral(): string {
    if (!this.estudiantes.length) {
      return '—';
    }
    const sum = this.estudiantes.reduce((acc, e) => acc + parseFloat(e.promedioReal || '0'), 0);
    return (sum / this.estudiantes.length).toFixed(1);
  }

  get enRiesgo(): number {
    return this.estudiantes.filter((e) => e.riesgo).length;
  }

  onImportExcel(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file || !this.selectedMateriaId) {
      return;
    }
    this.saving = true;
    this.facade.importCalificacionesExcel(this.selectedMateriaId, file).subscribe({
      next: () => {
        this.saving = false;
        this.successMessage = 'Calificaciones importadas.';
        this.loadConcentrado();
      },
      error: () => {
        this.saving = false;
        this.errorMessage = 'Error al importar el Excel.';
      },
    });
  }
}
