import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { finalize } from 'rxjs';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAdmin } from '../../../partials/bottom-navbar-admin/bottom-navbar-admin';
import { DocenteItem, DocentesService } from '../../../services/admin-services/docentes.service';

@Component({
  selector: 'app-docentes-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarAdmin],
  templateUrl: './docentes-screen.html',
  styleUrl: './docentes-screen.scss'
})
export class DocentesScreen implements OnInit {

  docentes: DocenteItem[] = [];
  searchTerm = '';
  currentPage = 1;
  pageSize = 5;
  totalItems = 0;
  totalPages = 1;
  isLoading = false;
  errorMessage = '';

  private readonly docentesService = inject(DocentesService);

  ngOnInit(): void {
    this.loadDocentes();
  }

  onSearch(searchValue: string): void {
    this.searchTerm = searchValue.trim();
    this.currentPage = 1;
    this.loadDocentes();
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.currentPage -= 1;
      this.loadDocentes();
    }
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage += 1;
      this.loadDocentes();
    }
  }

  onImportarDocentes(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) {
      return;
    }

    this.docentesService.importarDocentesPdf(file).subscribe({
      next: (result) => {
        alert(
          `Importacion completada. Creados: ${result.creados}, omitidos: ${result.omitidos}, errores: ${result.errores}`,
        );
        this.loadDocentes();
      },
      error: (err) => {
        alert(DocentesService.extractError(err, 'No se pudo importar el PDF de docentes.'));
      },
    });
    input.value = '';
  }

  eliminarDocente(docente: DocenteItem): void {
    const confirmado = confirm(`¿Eliminar al docente ${docente.nombre}?`);
    if (!confirmado) {
      return;
    }

    this.docentesService.deleteDocente(docente.id).subscribe({
      next: () => this.afterMutation(),
      error: (err) => {
        alert(DocentesService.extractError(err, 'No se pudo eliminar el docente.'));
      },
    });
  }

  trackByDocenteId(_: number, docente: DocenteItem): number {
    return docente.id;
  }

  get rangeStart(): number {
    if (!this.totalItems) {
      return 0;
    }

    return ((this.currentPage - 1) * this.pageSize) + 1;
  }

  get rangeEnd(): number {
    return Math.min(this.currentPage * this.pageSize, this.totalItems);
  }

  private afterMutation(): void {
    if (this.docentes.length === 1 && this.currentPage > 1) {
      this.currentPage -= 1;
    }

    this.loadDocentes();
  }

  private loadDocentes(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.docentesService.getDocentes({
      search: this.searchTerm,
      page: this.currentPage,
      pageSize: this.pageSize
    }).pipe(finalize(() => {
      this.isLoading = false;
    })).subscribe({
      next: (response) => {
        this.docentes = response.results;
        this.totalItems = response.count;
        this.totalPages = response.totalPages;
        this.currentPage = response.page;
        this.pageSize = response.pageSize;
      },
      error: (err) => {
        this.errorMessage = DocentesService.extractError(
          err,
          'No se pudo cargar el catalogo de docentes.',
        );
        this.docentes = [];
        this.totalItems = 0;
        this.totalPages = 1;
      },
    });
  }

}