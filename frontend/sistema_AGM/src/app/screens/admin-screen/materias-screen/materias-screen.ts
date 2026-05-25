import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize, forkJoin, map } from 'rxjs';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAdmin } from '../../../partials/bottom-navbar-admin/bottom-navbar-admin';
import { MateriaItem, MateriasService } from '../../../services/admin-services/materias.service';
import {
  PeriodoItem,
  PeriodosService,
} from '../../../services/admin-services/periodos.service';

@Component({
  selector: 'app-materias-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, TopbarAdmin, BottomNavbarAdmin],
  templateUrl: './materias-screen.html',
  styleUrl: './materias-screen.scss',
})
export class MateriasScreen implements OnInit {
  materias: MateriaItem[] = [];
  periodosOpciones: PeriodoItem[] = [];
  searchTerm = '';
  currentPage = 1;
  pageSize = 5;
  totalItems = 0;
  totalPages = 1;
  isLoading = false;
  errorMessage = '';
  periodoSeleccionadoId: number | null = null;
  periodoSeleccionadoNombre = '';
  isImporting = false;

  private readonly materiasService = inject(MateriasService);
  private readonly periodosService = inject(PeriodosService);

  ngOnInit(): void {
    this.cargarPeriodos();
  }

  onPeriodoChange(): void {
    this.currentPage = 1;
    this.actualizarNombrePeriodo();
    this.loadMaterias();
  }

  onSearch(searchValue: string): void {
    this.searchTerm = searchValue.trim();
    this.currentPage = 1;
    this.loadMaterias();
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.currentPage -= 1;
      this.loadMaterias();
    }
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage += 1;
      this.loadMaterias();
    }
  }

  trackByMateriaId(_: number, materia: MateriaItem): number {
    return materia.id;
  }

  eliminarMateria(materia: MateriaItem): void {
    const confirmado = confirm(
      `¿Eliminar la materia ${materia.nrc} — ${materia.nombre}?`,
    );
    if (!confirmado) {
      return;
    }

    this.materiasService.deleteMateria(materia.id).subscribe({
      next: () => {
        alert('Materia eliminada. Si vas a borrar el periodo, revisa que la columna Materias sea 0.');
        this.cargarPeriodos();
        this.loadMaterias();
      },
      error: (err) => {
        alert(MateriasService.extractError(err, 'No se pudo eliminar la materia.'));
      },
    });
  }

  onImportarMaterias(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) {
      return;
    }

    if (!this.periodoSeleccionadoId) {
      alert('Elige un periodo en el selector antes de importar.');
      input.value = '';
      return;
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('El archivo debe ser un PDF (programacion academica).');
      input.value = '';
      return;
    }

    this.isImporting = true;
    this.errorMessage = '';

    this.periodosService.importarMateriasPdf(this.periodoSeleccionadoId, file).subscribe({
      next: (resultado) => {
        this.isImporting = false;
        input.value = '';
        alert(
          `Importacion MS-2: ${resultado.creadas} materias nuevas, ` +
            `${resultado.actualizadas} actualizadas, ${resultado.errores} filas con error en el PDF.`,
        );
        this.cargarPeriodos();
        this.loadMaterias();
      },
      error: (err) => {
        this.isImporting = false;
        input.value = '';
        alert(
          PeriodosService.extractError(
            err,
            'No se pudo importar el PDF de materias.',
          ),
        );
      },
    });
  }

  get rangeStart(): number {
    if (!this.totalItems) {
      return 0;
    }
    return (this.currentPage - 1) * this.pageSize + 1;
  }

  get rangeEnd(): number {
    return Math.min(this.currentPage * this.pageSize, this.totalItems);
  }

  private cargarPeriodos(): void {
    this.periodosService.getPeriodos({ page: 1, pageSize: 100 }).subscribe({
      next: (page) => {
        if (!page.results.length) {
          this.periodosOpciones = [];
          this.loadMaterias();
          return;
        }

        forkJoin(
          page.results.map((periodo) =>
            this.materiasService.countByPeriodo(periodo.id).pipe(
              map((count) => ({ ...periodo, materiasCount: count })),
            ),
          ),
        ).subscribe({
          next: (enriquecidos) => {
            this.periodosOpciones = enriquecidos;
            if (!this.periodoSeleccionadoId) {
              const activo = enriquecidos.find((p) => p.activo);
              this.periodoSeleccionadoId = activo?.id ?? enriquecidos[0].id;
            }
            this.actualizarNombrePeriodo();
            this.loadMaterias();
          },
        });
      },
      error: () => {
        this.errorMessage = 'No se pudieron cargar los periodos.';
      },
    });
  }

  private actualizarNombrePeriodo(): void {
    const periodo = this.periodosOpciones.find((p) => p.id === this.periodoSeleccionadoId);
    this.periodoSeleccionadoNombre = periodo?.nombre ?? '';
  }

  private loadMaterias(): void {
    if (!this.periodoSeleccionadoId) {
      this.materias = [];
      this.errorMessage = 'Selecciona un periodo o crea uno en Administracion > Periodos.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    this.materiasService
      .getMaterias({
        search: this.searchTerm,
        page: this.currentPage,
        pageSize: this.pageSize,
        periodoId: this.periodoSeleccionadoId,
      })
      .pipe(finalize(() => {
        this.isLoading = false;
      }))
      .subscribe({
        next: (response) => {
          this.materias = response.results;
          this.totalItems = response.count;
          this.totalPages = response.totalPages;
          this.currentPage = response.page;
          this.pageSize = response.pageSize;
        },
        error: (err) => {
          this.errorMessage = PeriodosService.extractError(
            err,
            'No se pudo cargar el catalogo de materias.',
          );
          this.materias = [];
          this.totalItems = 0;
          this.totalPages = 1;
        },
      });
  }
}
