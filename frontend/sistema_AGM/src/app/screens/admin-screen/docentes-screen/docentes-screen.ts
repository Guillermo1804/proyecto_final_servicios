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
        const leidas = result.filas_leidas ?? 0;
        let msg = `Filas leidas del PDF: ${leidas}\nCreados: ${result.creados}\nOmitidos: ${result.omitidos}\nErrores: ${result.errores}`;

        if (leidas === 0 && result.creados === 0) {
          msg +=
            '\n\nEl PDF no trajo docentes en el formato esperado ' +
            '(tabla BUAP: Nombre | Correo | Ubicacion | Extension).\n' +
            'Si es programacion de materias (NRC), importala en Periodos (MS-2), no aqui.';
          const detalle = result.detalle_errores?.slice(0, 3) ?? [];
          if (detalle.length) {
            msg += '\n\nDetalle:\n' + detalle.map((d) => d.error ?? JSON.stringify(d)).join('\n');
          }
        }

        alert(msg);
        this.loadDocentes();
      },
      error: (err) => {
        alert(DocentesService.extractError(err, 'No se pudo importar el PDF de docentes.'));
      },
    });
    input.value = '';
  }

  activarDocente(docente: DocenteItem): void {
    if (docente.estado === 'Activo') {
      return;
    }

    const confirmado = confirm(
      `¿Activar acceso de ${docente.nombre}?\n\nSe creara o vinculara su usuario en MS-1 con el correo ${docente.correo}.`,
    );
    if (!confirmado) {
      return;
    }

    this.docentesService.activarDocente(docente.id).subscribe({
      next: () => {
        alert(
          `Docente activado. Puede iniciar sesion con ${docente.correo} ` +
            'y contraseña inicial = parte del correo antes de @.',
        );
        this.loadDocentes();
      },
      error: (err) => {
        alert(DocentesService.extractError(err, 'No se pudo activar el docente.'));
      },
    });
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