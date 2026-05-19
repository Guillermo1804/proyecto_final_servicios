import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { FacadeService } from '../../../services/facade.service';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

interface RubroEvaluacion {
  id?: number;
  nombre: string;
  descripcion: string;
  porcentaje: number;
}

interface ActividadUi {
  id?: number;
  titulo: string;
  descripcion: string;
  rubro: string;
  fechaEntrega: string;
  ponderacionId?: number;
}

@Component({
  selector: 'app-detalle-materia-screen',
  standalone: true,
  imports: [CommonModule, BottomNavbarDocente, TopbarAdmin, RouterLink, FormsModule],
  templateUrl: './detalle-materia-screen.html',
  styleUrl: './detalle-materia-screen.scss',
})
export class DetalleMateriaScreen implements OnInit {
  codigoMateria = '';
  materiaId = 0;
  loadingAlumnos = false;
  loadingPlan = false;
  savingPlan = false;
  planMessage = '';
  planError = '';

  alumnos: {
    iniciales: string;
    nombre: string;
    matricula: string;
    asistencia: string;
  }[] = [];

  constructor(
    private route: ActivatedRoute,
    private facade: FacadeService,
  ) {
    this.codigoMateria = this.route.snapshot.paramMap.get('id') ?? '';
    const id = Number(this.codigoMateria);
    this.materiaId = Number.isFinite(id) ? id : 0;
  }

  ngOnInit(): void {
    if (this.materiaId) {
      this.loadAlumnos();
      this.loadPlanEvaluacion();
      this.loadActividades();
    }
  }

  private loadAlumnos(): void {
    this.loadingAlumnos = true;
    forkJoin({
      body: this.facade.listAlumnosPorMateria(this.materiaId),
      asistencia: this.facade
        .getAsistenciaResumenMateria(this.materiaId)
        .pipe(catchError(() => of({ alumnos: [] }))),
    }).subscribe({
      next: ({ body, asistencia }) => {
        this.loadingAlumnos = false;
        const asistMap = new Map<number, number>();
        (asistencia.alumnos ?? []).forEach((row) => {
          if (row.alumno_id != null) {
            asistMap.set(row.alumno_id, row.porcentaje_asistencia ?? 0);
          }
        });
        const rows = this.facade.extractList<{
          alumno?: { id?: number; nombre?: string; apellido?: string; matricula?: string };
        }>(body);
        this.alumnos = rows.map((row) => {
          const a = row.alumno ?? {};
          const nombre = [a.apellido, a.nombre].filter(Boolean).join(', ') || '—';
          const ini = (a.nombre?.[0] ?? '') + (a.apellido?.[0] ?? '') || '?';
          const pct = a.id != null ? asistMap.get(a.id) : undefined;
          return {
            iniciales: ini.toUpperCase(),
            nombre,
            matricula: a.matricula ?? '—',
            asistencia: pct != null ? `${pct}%` : 'Sin registros',
          };
        });
      },
      error: () => {
        this.loadingAlumnos = false;
        this.alumnos = [];
      },
    });
  }

  tabActiva: 'alumnos' | 'evaluacion' | 'actividades' = 'alumnos';

  cambiarTab(tab: 'alumnos' | 'evaluacion' | 'actividades'): void {
    this.tabActiva = tab;
    if (tab === 'evaluacion' && !this.rubrosEvaluacion.length) {
      this.loadPlanEvaluacion();
    }
    if (tab === 'actividades') {
      this.loadActividades();
    }
  }

  rubrosEvaluacion: RubroEvaluacion[] = [];
  actividades: ActividadUi[] = [];

  nuevaActividad = {
    titulo: '',
    descripcion: '',
    rubro: '',
    fechaEntrega: '',
  };

  mostrarFormularioActividad = false;

  private loadPlanEvaluacion(): void {
    if (!this.materiaId) {
      return;
    }
    this.loadingPlan = true;
    this.planError = '';
    this.facade.getPonderaciones(this.materiaId).subscribe({
      next: (body) => {
        this.loadingPlan = false;
        const data = body?.data as {
          ponderaciones?: {
            id?: number;
            nombre_categoria?: string;
            porcentaje?: string | number;
          }[];
        };
        const items = data?.ponderaciones ?? [];
        if (items.length) {
          this.rubrosEvaluacion = items.map((p) => ({
            id: p.id,
            nombre: p.nombre_categoria ?? '',
            descripcion: '',
            porcentaje: Number(p.porcentaje ?? 0),
          }));
        } else if (!this.rubrosEvaluacion.length) {
          this.rubrosEvaluacion = [
            { nombre: 'Tareas', descripcion: '', porcentaje: 30 },
            { nombre: 'Examen', descripcion: '', porcentaje: 70 },
          ];
        }
      },
      error: () => {
        this.loadingPlan = false;
        if (!this.rubrosEvaluacion.length) {
          this.rubrosEvaluacion = [
            { nombre: 'Tareas', descripcion: '', porcentaje: 30 },
            { nombre: 'Examen', descripcion: '', porcentaje: 70 },
          ];
        }
      },
    });
  }

  private loadActividades(): void {
    if (!this.materiaId) {
      return;
    }
    this.facade.listActividades(this.materiaId).subscribe({
      next: (body) => {
        const data = body?.data as {
          categorias?: {
            categoria_nombre?: string;
            actividades?: {
              id?: number;
              nombre?: string;
              descripcion?: string;
              fecha?: string;
              ponderacion_id?: number;
            }[];
          }[];
        };
        this.actividades = [];
        (data?.categorias ?? []).forEach((cat) => {
          (cat.actividades ?? []).forEach((act) => {
            this.actividades.push({
              id: act.id,
              titulo: act.nombre ?? '—',
              descripcion: act.descripcion ?? '',
              rubro: cat.categoria_nombre ?? '',
              fechaEntrega: act.fecha ?? '',
              ponderacionId: act.ponderacion_id,
            });
          });
        });
      },
      error: () => {
        this.actividades = [];
      },
    });
  }

  abrirFormularioActividad(): void {
    this.mostrarFormularioActividad = true;
  }

  cancelarActividad(): void {
    this.mostrarFormularioActividad = false;
    this.nuevaActividad = { titulo: '', descripcion: '', rubro: '', fechaEntrega: '' };
  }

  crearActividad(): void {
    if (!this.nuevaActividad.titulo || !this.nuevaActividad.rubro) {
      alert('Completa el nombre de la actividad y el rubro.');
      return;
    }
    const rubro = this.rubrosEvaluacion.find((r) => r.nombre === this.nuevaActividad.rubro);
    if (!rubro?.id) {
      alert('Guarda primero el plan de evaluación (100%) para obtener IDs de rubros.');
      return;
    }
    this.facade
      .createActividad({
        ponderacion_id: rubro.id,
        nombre: this.nuevaActividad.titulo,
        descripcion: this.nuevaActividad.descripcion,
        fecha: this.nuevaActividad.fechaEntrega || null,
      })
      .subscribe({
        next: () => {
          this.cancelarActividad();
          this.loadActividades();
        },
        error: () => alert('No se pudo crear la actividad.'),
      });
  }

  get totalEvaluacion(): number {
    return this.rubrosEvaluacion.reduce((acc, item) => acc + Number(item.porcentaje), 0);
  }

  agregarRubro(): void {
    this.rubrosEvaluacion.push({ nombre: '', descripcion: '', porcentaje: 0 });
  }

  eliminarRubro(index: number): void {
    this.rubrosEvaluacion.splice(index, 1);
  }

  guardarPlanEvaluacion(): void {
    if (this.totalEvaluacion !== 100) {
      alert('El total debe ser exactamente 100%');
      return;
    }
    this.savingPlan = true;
    this.planError = '';
    this.planMessage = '';
    const ponderaciones = this.rubrosEvaluacion.map((r) => ({
      nombre_categoria: r.nombre.trim(),
      porcentaje: String(r.porcentaje),
    }));
    this.facade.savePonderaciones(this.materiaId, ponderaciones).subscribe({
      next: () => {
        this.savingPlan = false;
        this.planMessage = 'Plan de evaluación guardado en el servidor.';
        this.loadPlanEvaluacion();
      },
      error: () => {
        this.savingPlan = false;
        this.planError = 'No se pudo guardar el plan (revise que la suma sea 100%).';
      },
    });
  }
}
