import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { finalize, of, switchMap } from 'rxjs';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAdmin } from '../../../partials/bottom-navbar-admin/bottom-navbar-admin';
import { MateriaItem, MateriasService } from '../../../services/admin-services/materias.service';
import {
  PeriodosService,
} from '../../../services/admin-services/periodos.service';
import { AgmListPage } from '../../../services/tools/agm-api.helpers';

@Component({
  selector: 'app-materias-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarAdmin],
  templateUrl: './materias-screen.html',
  styleUrl: './materias-screen.scss'
})
export class MateriasScreen implements OnInit {

  materias: MateriaItem[] = [];
  searchTerm = '';
  currentPage = 1;
  pageSize = 5;
  totalItems = 0;
  totalPages = 1;
  isLoading = false;
  errorMessage = '';
  periodoActivoNombre = '';

  private readonly materiasService = inject(MateriasService);
  private readonly periodosService = inject(PeriodosService);

  ngOnInit(): void {
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

  get rangeStart(): number {
    if (!this.totalItems) {
      return 0;
    }

    return ((this.currentPage - 1) * this.pageSize) + 1;
  }

  get rangeEnd(): number {
    return Math.min(this.currentPage * this.pageSize, this.totalItems);
  }

  private loadMaterias(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.periodosService
      .getPeriodoActivo()
      .pipe(
        switchMap((periodoActivo) => {
          if (!periodoActivo) {
            this.periodoActivoNombre = '';
            this.errorMessage =
              'No hay periodo activo. Cree o active un periodo en Administracion > Periodos.';
            return of({
              results: [],
              count: 0,
              page: 1,
              pageSize: this.pageSize,
              totalPages: 1,
            } as AgmListPage<MateriaItem>);
          }

          this.periodoActivoNombre = periodoActivo.nombre;
          this.errorMessage = '';
          return this.materiasService.getMaterias({
            search: this.searchTerm,
            page: this.currentPage,
            pageSize: this.pageSize,
            periodoId: periodoActivo.id,
          });
        }),
        finalize(() => {
          this.isLoading = false;
        }),
      )
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