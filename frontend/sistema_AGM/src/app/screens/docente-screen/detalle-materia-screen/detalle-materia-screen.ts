import { CommonModule } from '@angular/common';
import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { MateriasDocenteService } from '../../../services/docente-services/materias-docente.service';
import { DetalleMateriaDocenteService, DetalleMateriaActividadBaseItem, DetalleMateriaActividadItem, DetalleMateriaAlumnoItem, DetalleMateriaRubroItem } from '../../../services/docente-services/detalle-materia-docente.service';
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

  busquedaAlumno = '';
  paginaActualAlumnos = 1;
  alumnosPorPagina = 2;
  paginaActualConcentrado = 1;
  alumnosPorPaginaConcentrado = 4;
  paginaActualActividades = 1;
  actividadesPorPagina = 2;
  alumnosPorPaginaActividad = 4;
  paginasAlumnosPorActividad: Record<number, number> = {};

  resumenMateria = { grupo: '', materia: '', horario: '' };

  constructor(
    private route: ActivatedRoute,
    private materiasService: MateriasDocenteService,
    private detalleMateriaService: DetalleMateriaDocenteService,
  ) {
    this.codigoMateria = this.route.snapshot.paramMap.get('id') ?? '';
    this.rubrosEvaluacion = this.detalleMateriaService.getRubrosEvaluacion();
    this.actividades = this.detalleMateriaService.getActividades();
    this.nuevaActividad = this.detalleMateriaService.crearActividadBase();
  }

  ngOnInit(): void {
    this.recalcularValoresInternosTodosRubros();
    this.loadMateriaContext();
    this.loadAlumnos();
  }

  private loadMateriaContext(): void {
    this.detalleMateriaService.loadResumenPorNrc(this.codigoMateria).subscribe({
      next: (resumen) => {
        this.resumenMateria = resumen;
      },
    });
  }

  private loadAlumnos(): void {
    this.alumnosLoading = true;
    this.alumnosError = '';
    this.detalleMateriaService.loadAlumnosPorNrc(this.codigoMateria).subscribe({
      next: (items) => {
        this.alumnos = items;
        this.alumnosLoading = false;
      },
      error: () => {
        this.alumnosError = 'No se pudieron cargar los alumnos inscritos (MS-3).';
        this.alumnos = [];
        this.alumnosLoading = false;
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
  return this.detalleMateriaService.generarPaginas(this.totalPaginasAlumnos);
}

get alumnosPaginados() {
  return this.detalleMateriaService.paginar(this.alumnosFiltrados, this.paginaActualAlumnos, this.alumnosPorPagina);
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

  const rubroActividad = this.nuevaActividad.rubro;

  this.actividades.push(this.detalleMateriaService.crearActividadConCalificaciones(this.alumnos, this.nuevaActividad));

  this.recalcularValoresInternosRubro(rubroActividad);
  this.paginaActualActividades = this.totalPaginasActividades;

  this.cancelarActividad();
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

setCalificacionActividad(actividad: { calificaciones: Record<string, number> }, matricula: string, valor: number | string): void {
  this.detalleMateriaService.setCalificacionActividad(actividad, matricula, valor);
}

onCalificacionInput(event: Event, actividad: { calificaciones: Record<string, number> }, matricula: string): void {
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

  if (!file) {
    return;
  }

  const actividad = this.actividadImportacionIndex >= 0 ? this.actividades[this.actividadImportacionIndex] : null;
  const nombreActividad = actividad?.titulo ?? 'actividad';

  alert(`Archivo ${file.name} seleccionado para ${nombreActividad}. Aquí se puede importar el Excel de calificaciones.`);
  input.value = '';
  this.actividadImportacionIndex = -1;
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

  const payload = {
    materia: this.codigoMateria,
    rubros: this.rubrosEvaluacion
  };

  console.log('Datos para backend:', payload);

  // después:
  // this.materiaService.guardarPlanEvaluacion(payload).subscribe(...)
}

abrirImportacionExcel(): void {
  this.excelInput?.nativeElement.click();
}

onExcelSeleccionado(event: Event): void {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];

  if (!file) {
    return;
  }

  alert(`Archivo ${file.name} seleccionado. Aquí se puede procesar el Excel para cargar el plan de evaluación.`);
  input.value = '';
}
cerrarMateria(): void {
  const confirmar = confirm('¿Cerrar la materia y marcarla como "Terminado"? Esta acción se puede revertir manualmente.');
  if (!confirmar) {
    return;
  }

  this.materiasService.updateMateriaEstado(this.codigoMateria, 'Terminado').subscribe((res) => {
    alert('Materia marcada como Terminado.');
  }, () => {
    alert('No se pudo actualizar el estado en el servidor. Estado local actualizado.');
  });
}

imprimirListaNotas(): void {
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