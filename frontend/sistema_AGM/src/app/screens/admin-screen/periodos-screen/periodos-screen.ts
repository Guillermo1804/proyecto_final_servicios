import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NavigationEnd, Router } from '@angular/router';
import { filter, finalize, forkJoin, map, of, switchMap } from 'rxjs';
import { Subscription } from 'rxjs';
import { BottomNavbarAdmin } from '../../../partials/bottom-navbar-admin/bottom-navbar-admin';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { MateriasService } from '../../../services/admin-services/materias.service';
import { PeriodoFormValue, PeriodoItem, PeriodoTemporada, PeriodosService } from '../../../services/admin-services/periodos.service';

type TemporadaFiltro = PeriodoTemporada | 'Todos';

interface PeriodoFormModel {
  temporada: PeriodoTemporada;
  anio: number;
  fechaInicio: string;
  fechaFin: string;
}

@Component({
  selector: 'app-periodos-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, TopbarAdmin, BottomNavbarAdmin],
  templateUrl: './periodos-screen.html',
  styleUrl: './periodos-screen.scss'
})
export class PeriodosScreen implements OnInit, OnDestroy {

  periodos: PeriodoItem[] = [];
  periodoActivoActual: PeriodoItem | null = null;
  temporadasFiltro: Array<{ label: string; value: TemporadaFiltro }> = [
    { label: 'Todos', value: 'Todos' },
    { label: 'Primavera', value: 'Primavera' },
    { label: 'Verano', value: 'Verano' },
    { label: 'Otoño', value: 'Otoño' }
  ];

  searchTerm = '';
  temporadaSeleccionada: TemporadaFiltro = 'Todos';
  mostrarFormulario = false;
  editandoId: number | null = null;
  isLoading = false;
  errorMessage = '';
  totalItems = 0;
  totalPages = 1;
  currentPage = 1;
  pageSize = 12;
  nuevoPeriodo = this.crearPeriodoVacio();

  private readonly periodosService = inject(PeriodosService);
  private readonly materiasService = inject(MateriasService);
  private readonly router = inject(Router);
  private routerSub?: Subscription;

  ngOnInit(): void {
    this.loadPeriodos();
    this.loadPeriodoActivo();
    this.routerSub = this.router.events
      .pipe(filter((e) => e instanceof NavigationEnd))
      .subscribe((e) => {
        const url = (e as NavigationEnd).urlAfterRedirects;
        if (url.includes('/admin/periodos')) {
          this.loadPeriodos();
          this.loadPeriodoActivo();
        }
      });
  }

  ngOnDestroy(): void {
    this.routerSub?.unsubscribe();
  }

  abrirFormulario(): void {
    this.mostrarFormulario = true;
  }

  cancelarFormulario(): void {
    this.mostrarFormulario = false;
    this.editandoId = null;
    this.nuevoPeriodo = this.crearPeriodoVacio();
  }

  aplicarFiltros(): void {
    this.currentPage = 1;
    this.loadPeriodos();
  }

  cambiarTemporada(temporada: TemporadaFiltro): void {
    this.temporadaSeleccionada = temporada;
    this.aplicarFiltros();
  }

  limpiarFiltros(): void {
    this.searchTerm = '';
    this.temporadaSeleccionada = 'Todos';
    this.aplicarFiltros();
  }

  guardarPeriodo(): void {
    if (!this.nuevoPeriodo.fechaInicio || !this.nuevoPeriodo.fechaFin) {
      alert('Completa la fecha de inicio y la fecha de fin.');
      return;
    }

    const fechaInicio = new Date(this.nuevoPeriodo.fechaInicio).getTime();
    const fechaFin = new Date(this.nuevoPeriodo.fechaFin).getTime();

    if (Number.isNaN(fechaInicio) || Number.isNaN(fechaFin) || fechaInicio >= fechaFin) {
      alert('La fecha de inicio debe ser anterior a la fecha de fin.');
      return;
    }

    const payload: PeriodoFormValue = {
      temporada: this.nuevoPeriodo.temporada,
      anio: this.nuevoPeriodo.anio,
      fechaInicio: this.nuevoPeriodo.fechaInicio,
      fechaFin: this.nuevoPeriodo.fechaFin,
      planEstudios: `Plan ${this.nuevoPeriodo.anio}`,
      activo: false
    };

    const request = this.editandoId
      ? this.periodosService.updatePeriodo(this.editandoId, payload)
      : this.periodosService.createPeriodo(payload);

    request.subscribe({
      next: () => {
        this.cancelarFormulario();
        this.afterMutation();
      },
      error: (err) => {
        alert(PeriodosService.extractError(err, 'No se pudo guardar el periodo.'));
      },
    });
  }

  editarPeriodo(periodo: PeriodoItem): void {
    this.editandoId = periodo.id;
    this.nuevoPeriodo = {
      temporada: periodo.temporada,
      anio: periodo.anio,
      fechaInicio: periodo.fechaInicio,
      fechaFin: periodo.fechaFin
    };
    this.mostrarFormulario = true;
  }

  eliminarPeriodo(periodo: PeriodoItem): void {
    if (periodo.materiasCount > 0) {
      alert(
        `El periodo "${periodo.nombre}" todavía tiene ${periodo.materiasCount} materia(s) en la base de datos.\n\n` +
          'Ve a Administración → Materias, elige ese periodo en el selector y bórralas todas. ' +
          'La pantalla de Materias antes solo mostraba el periodo activo.',
      );
      return;
    }

    const confirmado = confirm(`¿Deseas eliminar el periodo ${periodo.nombre}?`);

    if (!confirmado) {
      return;
    }

    this.periodosService.deletePeriodo(periodo.id).subscribe({
      next: () => this.afterMutation(),
      error: (err) => {
        alert(PeriodosService.extractError(err, 'No se pudo eliminar el periodo.'));
      },
    });
  }

  cambiarEstado(periodo: PeriodoItem): void {
    if (periodo.activo) {
      alert(
        'Para desactivar este periodo, active otro periodo desde la lista. El backend solo permite un periodo activo.',
      );
      return;
    }

    this.periodosService.activarPeriodo(periodo.id).subscribe({
      next: () => this.afterMutation(),
      error: (err) => {
        alert(PeriodosService.extractError(err, 'No se pudo activar el periodo.'));
      },
    });
  }

  trackByPeriodoId(_: number, periodo: PeriodoItem): number {
    return periodo.id;
  }

  get botonFormularioTexto(): string {
    return this.editandoId ? 'Actualizar Periodo' : 'Guardar Periodo';
  }

  get periodoNombrePreview(): string {
    return `${this.nuevoPeriodo.temporada} ${this.nuevoPeriodo.anio}`;
  }

  get temporadaSeleccionadaEtiqueta(): string {
    return this.temporadaSeleccionada === 'Todos' ? 'Todas' : this.temporadaSeleccionada;
  }

  private afterMutation(): void {
    this.loadPeriodos();
    this.loadPeriodoActivo();
  }

  private loadPeriodos(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.periodosService
      .getPeriodos({
        search: this.searchTerm.trim(),
        temporada: this.temporadaSeleccionada,
        page: this.currentPage,
        pageSize: this.pageSize,
      })
      .pipe(
        switchMap((response) => this.enriquecerConteoMaterias(response.results).pipe(
          map((results) => ({ ...response, results })),
        )),
        finalize(() => {
          this.isLoading = false;
        }),
      )
      .subscribe({
      next: (response) => {
        this.periodos = response.results;
        this.totalItems = response.count;
        this.totalPages = response.totalPages;
        this.currentPage = response.page;
        this.pageSize = response.pageSize;
      },
      error: (err) => {
        this.errorMessage = PeriodosService.extractError(
          err,
          'No se pudo cargar el catalogo de periodos.',
        );
        this.periodos = [];
        this.totalItems = 0;
        this.totalPages = 1;
      },
    });
  }

  private loadPeriodoActivo(): void {
    this.periodosService.getPeriodoActivo().subscribe({
      next: (periodo) => {
        this.periodoActivoActual = periodo;
      },
      error: () => {
        this.periodoActivoActual = null;
      }
    });
  }

  private enriquecerConteoMaterias(periodos: PeriodoItem[]) {
    if (!periodos.length) {
      return of([] as PeriodoItem[]);
    }

    return forkJoin(
      periodos.map((periodo) =>
        this.materiasService.countByPeriodo(periodo.id).pipe(
          map((count) => ({
            ...periodo,
            materiasCount: count,
          })),
        ),
      ),
    );
  }

  private crearPeriodoVacio(): PeriodoFormModel {
    return {
      temporada: 'Primavera',
      anio: new Date().getFullYear(),
      fechaInicio: '',
      fechaFin: ''
    };
  }

}
