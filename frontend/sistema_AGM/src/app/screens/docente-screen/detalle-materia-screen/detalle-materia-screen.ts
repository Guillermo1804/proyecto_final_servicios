import { CommonModule } from '@angular/common';
import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CalificacionesService } from '../../../services/docente-services/calificaciones.service';
import { MateriasDocenteService } from '../../../services/docente-services/materias-docente.service';
import { DetalleMateriaDocenteService, DetalleMateriaActividadBaseItem, DetalleMateriaActividadItem, DetalleMateriaAlumnoItem, DetalleMateriaRubroItem } from '../../../services/docente-services/detalle-materia-docente.service';
import { AlumnosService } from '../../../services/alumno-services/alumnos.service';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-detalle-materia-screen',
  standalone: true,
  imports: [CommonModule, BottomNavbarDocente, TopbarAdmin,RouterLink,FormsModule],
  templateUrl: './detalle-materia-screen.html',
  styleUrl: './detalle-materia-screen.scss'
})
export class DetalleMateriaScreen implements OnInit {

  codigoMateria = '';
  alumnos: DetalleMateriaAlumnoItem[] = [];
  alumnosLoading = false;
  alumnosError = '';
  procesandoMs1AlumnoId: number | null = null;

  busquedaAlumno = '';
  paginaActualAlumnos = 1;
  alumnosPorPagina = 5;
  paginaActualConcentrado = 1;
  alumnosPorPaginaConcentrado = 4;
  paginaActualActividades = 1;
  actividadesPorPagina = 2;
  alumnosPorPaginaActividad = 4;
  paginasAlumnosPorActividad: Record<number, number> = {};

  resumenMateria = { grupo: '', materia: '', horario: '' };

  materiaId: number | null = null;
  evaluacionLoading = false;
  evaluacionError = '';
  listaImpresa = false;
  guardandoPlan = false;
  guardandoCalificacion = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private materiasService: MateriasDocenteService,
    private detalleMateriaService: DetalleMateriaDocenteService,
    private calificacionesService: CalificacionesService,
    private alumnosService: AlumnosService,
  ) {
    this.codigoMateria = this.route.snapshot.paramMap.get('id') ?? '';
    this.nuevaActividad = this.detalleMateriaService.crearActividadBase();
  }

  ngOnInit(): void {
    this.loadMateriaContext();
    this.loadAlumnos();
  }

  irImportarAlumnos(): void {
    void this.router.navigate(
      ['/docente/materias', this.codigoMateria, 'importar-alumnos'],
      {
        state: {
          materiaId: this.materiaId,
          materiaNombre: this.resumenMateria.materia || this.codigoMateria,
        },
      },
    );
  }

  private loadMateriaContext(): void {
    this.detalleMateriaService.loadResumenPorNrc(this.codigoMateria).subscribe({
      next: (resumen) => {
        this.resumenMateria = resumen;
      },
      error: () => {
        this.resumenMateria = {
          grupo: this.codigoMateria,
          materia: 'Materia',
          horario: '',
        };
      },
    });
  }

  get totalAlumnosInscritos(): number {
    return this.alumnos.length;
  }

  get promedioGrupal(): string {
    const conPromedio = this.alumnos.filter((a) => (a.promedioRedondeado ?? 0) > 0);
    if (!conPromedio.length) {
      return '—';
    }
    const suma = conPromedio.reduce((acc, a) => acc + (a.promedioRedondeado ?? 0), 0);
    return (suma / conPromedio.length).toFixed(2);
  }

  private loadAlumnos(): void {
    this.alumnosLoading = true;
    this.alumnosError = '';
    this.detalleMateriaService.loadAlumnosPorNrc(this.codigoMateria).subscribe({
      next: (items) => {
        this.alumnos = items;
        this.alumnosLoading = false;
        this.loadEvaluacion();
      },
      error: () => {
        this.alumnosError = 'No se pudieron cargar los alumnos inscritos (MS-3).';
        this.alumnos = [];
        this.alumnosLoading = false;
      },
    });
  }

  private loadEvaluacion(): void {
    this.evaluacionLoading = true;
    this.evaluacionError = '';
    this.detalleMateriaService.loadEvaluacionPorNrc(this.codigoMateria).subscribe({
      next: (bundle) => {
        this.materiaId = bundle.materiaId;
        this.rubrosEvaluacion = bundle.rubros;
        this.actividades = bundle.actividades;
        this.recalcularValoresInternosTodosRubros();
        this.evaluacionLoading = false;
      },
      error: () => {
        this.evaluacionError = 'No se pudo cargar el plan de evaluacion (MS-4).';
        this.rubrosEvaluacion = [];
        this.actividades = [];
        this.evaluacionLoading = false;
      },
    });
  }

  tabActiva: 'alumnos' | 'evaluacion' | 'actividades' = 'alumnos';

cambiarTab(tab: 'alumnos' | 'evaluacion' | 'actividades'): void {
  this.tabActiva = tab;
}

buscarAlumnos(termino: string): void {
  this.busquedaAlumno = termino;
  this.paginaActualAlumnos = 1;
}

get alumnosFiltrados() {
  return this.detalleMateriaService.filtrarAlumnos(this.alumnos, this.busquedaAlumno);
}

get totalPaginasAlumnos(): number {
  return this.detalleMateriaService.getTotalPaginas(this.alumnosFiltrados.length, this.alumnosPorPagina);
}

get paginasAlumnos(): number[] {
  return this.detalleMateriaService.generarPaginasVentana(
    this.totalPaginasAlumnos,
    this.paginaActualAlumnos,
  );
}

get alumnosPaginados() {
  return this.detalleMateriaService.paginar(this.alumnosFiltrados, this.paginaActualAlumnos, this.alumnosPorPagina);
}

get alumnosDesdeRegistro(): number {
  if (!this.alumnosFiltrados.length) {
    return 0;
  }
  return (this.paginaActualAlumnos - 1) * this.alumnosPorPagina + 1;
}

get alumnosHastaRegistro(): number {
  return Math.min(this.paginaActualAlumnos * this.alumnosPorPagina, this.alumnosFiltrados.length);
}

esEmailPlaceholder(email: string): boolean {
  const value = (email || '').trim().toLowerCase();
  return value.endsWith('@alumno.buap.mx') && /^\d{8,9}@alumno\.buap\.mx$/.test(value);
}

puedeDesactivarAlumno(alumno: DetalleMateriaAlumnoItem): boolean {
  return alumno.alumnoId != null && alumno.usuarioId != null;
}

puedeActivarAlumno(alumno: DetalleMateriaAlumnoItem): boolean {
  return (
    alumno.alumnoId != null &&
    alumno.usuarioId == null &&
    !!alumno.email &&
    alumno.email !== '—'
  );
}

desactivarAlumno(alumno: DetalleMateriaAlumnoItem): void {
  if (!this.puedeDesactivarAlumno(alumno) || !alumno.alumnoId) {
    return;
  }

  const confirmado = confirm(
    `¿Desactivar acceso de ${alumno.nombre} en MS-1?\n\nYa no podra iniciar sesion hasta que lo reactives.`,
  );
  if (!confirmado) {
    return;
  }

  this.procesandoMs1AlumnoId = alumno.alumnoId;
  this.alumnosService.desactivarAlumno(alumno.alumnoId).subscribe({
    next: () => {
      this.procesandoMs1AlumnoId = null;
      alert(`Acceso desactivado para ${alumno.nombre}.`);
      this.loadAlumnos();
    },
    error: (err) => {
      this.procesandoMs1AlumnoId = null;
      alert(AlumnosService.extractError(err, 'No se pudo desactivar el alumno.'));
    },
  });
}

activarAlumno(alumno: DetalleMateriaAlumnoItem): void {
  if (!this.puedeActivarAlumno(alumno) || !alumno.alumnoId) {
    return;
  }

  const confirmado = confirm(
    `¿Reactivar acceso de ${alumno.nombre}?\n\nSe creara o vinculara su usuario en MS-1 con ${alumno.email}.`,
  );
  if (!confirmado) {
    return;
  }

  this.procesandoMs1AlumnoId = alumno.alumnoId;
  this.alumnosService.activarAlumno(alumno.alumnoId).subscribe({
    next: () => {
      this.procesandoMs1AlumnoId = null;
      alert(
        `Alumno reactivado. Puede iniciar sesion con ${alumno.email} ` +
          'y contraseña inicial = parte del correo antes de @.',
      );
      this.loadAlumnos();
    },
    error: (err) => {
      this.procesandoMs1AlumnoId = null;
      alert(AlumnosService.extractError(err, 'No se pudo activar el alumno.'));
    },
  });
}

irAPaginaAlumnos(pagina: number): void {
  this.paginaActualAlumnos = Math.min(Math.max(pagina, 1), this.totalPaginasAlumnos);
}

paginaAnteriorAlumnos(): void {
  this.irAPaginaAlumnos(this.paginaActualAlumnos - 1);
}

paginaSiguienteAlumnos(): void {
  this.irAPaginaAlumnos(this.paginaActualAlumnos + 1);
}
  rubrosEvaluacion: DetalleMateriaRubroItem[] = [];

  actividades: DetalleMateriaActividadItem[] = [];

  nuevaActividad: DetalleMateriaActividadBaseItem = {
    titulo: '',
    descripcion: '',
    rubro: '',
    fechaEntrega: '',
    estado: 'Abierta',
    tipo: 'abierta',
    entregas: 0
  };

  mostrarFormularioActividad = false;

  @ViewChild('excelInput') private excelInput?: ElementRef<HTMLInputElement>;
  @ViewChild('actividadExcelInput') private actividadExcelInput?: ElementRef<HTMLInputElement>;
  actividadImportacionIndex = -1;

abrirFormularioActividad(): void {
  this.mostrarFormularioActividad = true;
}

cancelarActividad(): void {
  this.mostrarFormularioActividad = false;

  this.nuevaActividad = this.detalleMateriaService.crearActividadBase();
}

crearActividad(): void {
  if (!this.nuevaActividad.titulo || !this.nuevaActividad.rubro) {
    alert('Completa el nombre de la actividad y el rubro.');
    return;
  }

  if (!this.materiaId) {
    alert('No se encontro la materia en el sistema.');
    return;
  }

  const rubroActividad = this.nuevaActividad.rubro;

  this.detalleMateriaService
    .crearActividadRemota(this.rubrosEvaluacion, this.nuevaActividad, this.alumnos)
    .subscribe({
      next: (actividad) => {
        this.actividades.push(actividad);
        this.recalcularValoresInternosRubro(rubroActividad);
        this.paginaActualActividades = this.totalPaginasActividades;
        this.cancelarActividad();
      },
      error: (err) => {
        const msg =
          err instanceof Error
            ? err.message
            : this.calificacionesService.mapApiError(err, 'No se pudo crear la actividad.');
        alert(msg);
      },
    });
}

recalcularValoresInternosTodosRubros(): void {
  this.detalleMateriaService.recalcularValoresInternosTodosRubros(this.actividades);
}

recalcularValoresInternosRubro(rubro: string): void {
  this.detalleMateriaService.recalcularValoresInternosRubro(this.actividades, rubro);
}

get valorTotalRubros(): number {
  return this.detalleMateriaService.getValorTotalRubros(this.rubrosEvaluacion);
}

get valorTotalActividadesPorRubro(): Record<string, number> {
  return this.detalleMateriaService.getValorTotalActividadesPorRubro(this.actividades);
}

getPesoActividad(actividad: { rubro: string; valorInterno: number }): number {
  return this.detalleMateriaService.getPesoActividad(actividad, this.rubrosEvaluacion, this.valorTotalActividadesPorRubro);
}

obtenerCalificacionActividad(actividad: { calificaciones?: Record<string, number> }, matricula: string): number {
  return this.detalleMateriaService.obtenerCalificacionActividad(actividad, matricula);
}

setCalificacionActividad(actividad: DetalleMateriaActividadItem, matricula: string, valor: number | string): void {
  this.detalleMateriaService.setCalificacionActividad(actividad, matricula, valor);
}

guardarCalificacionEnServidor(actividad: DetalleMateriaActividadItem, alumno: DetalleMateriaAlumnoItem, valor: number | string): void {
  if (this.listaImpresa) {
    alert('La lista ya fue impresa: no se pueden editar calificaciones.');
    return;
  }
  this.guardandoCalificacion = true;
  this.detalleMateriaService.persistirCalificacion(actividad, alumno, valor).subscribe({
    next: () => {
      this.guardandoCalificacion = false;
      if (this.materiaId) {
        this.detalleMateriaService.recargarConcentrado(this.materiaId).subscribe({
          next: (alumnos) => {
            this.alumnos = alumnos;
          },
        });
      }
    },
    error: (err) => {
      this.guardandoCalificacion = false;
      alert(this.calificacionesService.mapApiError(err, 'No se pudo guardar la calificacion.'));
    },
  });
}

onCalificacionInput(event: Event, actividad: DetalleMateriaActividadItem, matricula: string): void {
  const input = event.target as HTMLInputElement;
  const calificacion = this.detalleMateriaService.setCalificacionActividad(actividad, matricula, input.value);
  input.value = String(calificacion);
}

getPaginaActualAlumnosActividad(actividadIndex: number): number {
  return this.paginasAlumnosPorActividad[actividadIndex] ?? 1;
}

getTotalPaginasAlumnosActividad(): number {
  return this.detalleMateriaService.getTotalPaginas(this.alumnos.length, this.alumnosPorPaginaActividad);
}

getPaginasAlumnosActividad(): number[] {
  return this.detalleMateriaService.generarPaginas(this.getTotalPaginasAlumnosActividad());
}

getAlumnosActividadPaginados(actividadIndex: number) {
  const paginaActual = this.getPaginaActualAlumnosActividad(actividadIndex);
  return this.detalleMateriaService.paginar(this.alumnos, paginaActual, this.alumnosPorPaginaActividad);
}

irAPaginaAlumnosActividad(actividadIndex: number, pagina: number): void {
  const total = this.getTotalPaginasAlumnosActividad();
  this.paginasAlumnosPorActividad[actividadIndex] = Math.min(Math.max(pagina, 1), total);
}

paginaAnteriorAlumnosActividad(actividadIndex: number): void {
  this.irAPaginaAlumnosActividad(actividadIndex, this.getPaginaActualAlumnosActividad(actividadIndex) - 1);
}

paginaSiguienteAlumnosActividad(actividadIndex: number): void {
  this.irAPaginaAlumnosActividad(actividadIndex, this.getPaginaActualAlumnosActividad(actividadIndex) + 1);
}

get totalPaginasConcentrado(): number {
  return this.detalleMateriaService.getTotalPaginas(this.concentradoCalificaciones.length, this.alumnosPorPaginaConcentrado);
}

get paginasConcentrado(): number[] {
  return this.detalleMateriaService.generarPaginas(this.totalPaginasConcentrado);
}

get concentradoCalificacionesPaginado() {
  return this.detalleMateriaService.paginar(this.concentradoCalificaciones, this.paginaActualConcentrado, this.alumnosPorPaginaConcentrado);
}

irAPaginaConcentrado(pagina: number): void {
  this.paginaActualConcentrado = Math.min(Math.max(pagina, 1), this.totalPaginasConcentrado);
}

paginaAnteriorConcentrado(): void {
  this.irAPaginaConcentrado(this.paginaActualConcentrado - 1);
}

paginaSiguienteConcentrado(): void {
  this.irAPaginaConcentrado(this.paginaActualConcentrado + 1);
}

get totalPaginasActividades(): number {
  return this.detalleMateriaService.getTotalPaginas(this.actividades.length, this.actividadesPorPagina);
}

get paginasActividades(): number[] {
  return this.detalleMateriaService.generarPaginas(this.totalPaginasActividades);
}

get actividadesPaginadas(): DetalleMateriaActividadItem[] {
  return this.detalleMateriaService.paginar(this.actividades, this.paginaActualActividades, this.actividadesPorPagina);
}

irAPaginaActividades(pagina: number): void {
  this.paginaActualActividades = Math.min(Math.max(pagina, 1), this.totalPaginasActividades);
}

paginaAnteriorActividades(): void {
  this.irAPaginaActividades(this.paginaActualActividades - 1);
}

paginaSiguienteActividades(): void {
  this.irAPaginaActividades(this.paginaActualActividades + 1);
}

abrirImportacionCalificaciones(index: number): void {
  this.actividadImportacionIndex = index;
  this.actividadExcelInput?.nativeElement.click();
}

onCalificacionesExcelSeleccionado(event: Event): void {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];

  if (!file || !this.materiaId) {
    return;
  }

  this.detalleMateriaService.importarCalificacionesExcel(this.materiaId, file).subscribe({
    next: (resumen) => {
      alert(
        `Importacion MS-4: ${resumen.importadas} calificaciones guardadas, ${resumen.fallos} fallos.`,
      );
      this.loadEvaluacion();
      input.value = '';
      this.actividadImportacionIndex = -1;
    },
    error: (err) => {
      alert(this.calificacionesService.mapApiError(err, 'No se pudo importar el Excel.'));
      input.value = '';
      this.actividadImportacionIndex = -1;
    },
  });
}

get promedioPonderadoReal(): number {
  return this.detalleMateriaService.getPromedioPonderadoReal(this.alumnos, this.actividades, this.rubrosEvaluacion);
}

get promedioPonderadoRedondeado(): number {
  return this.detalleMateriaService.getPromedioPonderadoRedondeado(this.alumnos, this.actividades, this.rubrosEvaluacion);
}

get concentradoCalificaciones() {
  return this.detalleMateriaService.getConcentradoCalificaciones(this.alumnos, this.actividades, this.rubrosEvaluacion);
}

calcularPromedioAlumno(matricula: string): number {
  return this.detalleMateriaService.calcularPromedioAlumno(matricula, this.actividades, this.rubrosEvaluacion);
}

get totalEvaluacion(): number {
  return this.detalleMateriaService.getValorTotalRubros(this.rubrosEvaluacion);
}

get planEvaluacionValido(): boolean {
  return this.detalleMateriaService.getPlanEvaluacionValido(this.rubrosEvaluacion);
}

agregarRubro(): void {

  this.rubrosEvaluacion.push({
    nombre: '',
    descripcion: '',
    porcentaje: 0
  });

}

getMaximoRubro(index: number): number {
  return this.detalleMateriaService.getMaximoRubro(this.rubrosEvaluacion, index);
}

limitarPorcentajeRubro(index: number): void {
  this.detalleMateriaService.limitarPorcentajeRubro(this.rubrosEvaluacion, index);
}

eliminarRubro(index: number): void {
  this.rubrosEvaluacion.splice(index, 1);
}
guardarPlanEvaluacion(): void {
  if (!this.planEvaluacionValido) {
    alert(`El total de la evaluación debe sumar 100%. Actualmente suma ${this.totalEvaluacion}%.`);
    return;
  }

  if (!this.materiaId) {
    alert('No se encontro la materia en el sistema.');
    return;
  }

  this.guardandoPlan = true;
  this.detalleMateriaService.guardarPlanEvaluacion(this.materiaId, this.rubrosEvaluacion).subscribe({
    next: (rubros) => {
      this.rubrosEvaluacion = rubros;
      this.guardandoPlan = false;
      alert('Plan de evaluacion guardado en MS-4.');
    },
    error: (err) => {
      this.guardandoPlan = false;
      alert(this.calificacionesService.mapApiError(err, 'No se pudo guardar el plan de evaluacion.'));
    },
  });
}

abrirImportacionExcel(): void {
  this.excelInput?.nativeElement.click();
}

onExcelSeleccionado(event: Event): void {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];

  if (!file || !this.materiaId) {
    return;
  }

  this.detalleMateriaService.importarPlanEvaluacionExcel(this.materiaId, file).subscribe({
    next: (rubros) => {
      this.rubrosEvaluacion = rubros;
      alert('Plan de evaluacion importado desde Excel (MS-4).');
      input.value = '';
    },
    error: (err) => {
      alert(this.calificacionesService.mapApiError(err, 'No se pudo importar el plan.'));
      input.value = '';
    },
  });
}
cerrarMateria(): void {
  const confirmar = confirm(
    '¿Cerrar la materia? Se publicaran las calificaciones (MS-4) y se avisara por correo a los alumnos inscritos (MS-6).',
  );
  if (!confirmar || !this.materiaId) {
    return;
  }

  this.detalleMateriaService.cerrarMateriaCalificaciones(this.materiaId).subscribe({
    next: () => {
      alert('Materia cerrada. Los alumnos recibiran un correo de aviso en breve (MS-6).');
      this.materiasService.updateMateriaEstado(this.codigoMateria, 'Terminado').subscribe({
        next: () => undefined,
        error: () => undefined,
      });
    },
    error: (err) => {
      alert(this.calificacionesService.mapApiError(err, 'No se pudo cerrar la materia.'));
    },
  });
}

imprimirListaNotas(): void {
  if (!this.materiaId) {
    alert('Materia no disponible.');
    return;
  }

  this.detalleMateriaService.marcarListaImpresa(this.materiaId).subscribe({
    next: () => {
      this.listaImpresa = true;
      this.abrirVentanaImpresionConcentrado();
    },
    error: (err) => {
      alert(this.calificacionesService.mapApiError(err, 'No se pudo marcar la lista como impresa.'));
    },
  });
}

private abrirVentanaImpresionConcentrado(): void {
  const title = `Concentrado de calificaciones - ${this.codigoMateria}`;
  const cols = ['Alumno', 'Matrícula', 'Promedio real', 'Promedio redondeado'];

  const rows = this.concentradoCalificaciones.map((a) => `
    <tr>
      <td>${a.nombre}</td>
      <td>${a.matricula}</td>
      <td>${Number(a.promedioReal).toFixed(2)}</td>
      <td>${a.promedioRedondeado}</td>
    </tr>
  `).join('');

  const html = `
    <html>
      <head>
        <title>${title}</title>
        <style>
          body{font-family: Arial, Helvetica, sans-serif; padding:20px}
          table{width:100%;border-collapse:collapse}
          th,td{border:1px solid #ddd;padding:8px;text-align:left}
          th{background:#f3f4f6}
        </style>
      </head>
      <body>
        <h2>${title}</h2>
        <table>
          <thead>
            <tr>
              <th>${cols[0]}</th>
              <th>${cols[1]}</th>
              <th>${cols[2]}</th>
              <th>${cols[3]}</th>
            </tr>
          </thead>
          <tbody>
            ${rows}
          </tbody>
        </table>
      </body>
    </html>
  `;

  const w = window.open('', '_blank');
  if (!w) {
    alert('No fue posible abrir la ventana de impresión.');
    return;
  }

  w.document.write(html);
  w.document.close();
  w.focus();
  setTimeout(() => w.print(), 300);
}
}