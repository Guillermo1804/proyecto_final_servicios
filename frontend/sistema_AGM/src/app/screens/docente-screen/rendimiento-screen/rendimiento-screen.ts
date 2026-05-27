import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { finalize } from 'rxjs';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import {
  RendimientoDocenteService,
  RendimientoEstudianteItem,
} from '../../../services/docente-services/rendimiento-docente.service';

@Component({
  selector: 'app-rendimiento-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './rendimiento-screen.html',
  styleUrl: './rendimiento-screen.scss',
})
export class RendimientoScreen implements OnInit {
  codigoMateria = '';
  estudiantesRiesgo: RendimientoEstudianteItem[] = [];
  totalEstudiantesRiesgo = 0;
  currentPage = 1;
  pageSize = 10;
  totalPages = 1;
  isLoading = true;
  loadError = '';

  constructor(
    private route: ActivatedRoute,
    private readonly rendimientoService: RendimientoDocenteService,
  ) {
    this.codigoMateria = this.route.snapshot.paramMap.get('id') ?? '';
  }

  ngOnInit(): void {
    if (!this.codigoMateria) {
      this.isLoading = false;
      this.loadError = 'NRC de materia no encontrado en la ruta.';
      return;
    }

    this.rendimientoService
      .loadEstudiantesRiesgoPorNrc(this.codigoMateria)
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (rows) => {
          this.estudiantesRiesgo = rows;
          this.totalEstudiantesRiesgo = rows.length;
          this.totalPages = this.rendimientoService.getTotalPages(
            this.totalEstudiantesRiesgo,
            this.pageSize,
          );
        },
        error: () => {
          this.loadError = 'No se pudo cargar el rendimiento de alumnos (MS-4).';
          this.estudiantesRiesgo = [];
        },
      });
  }

  get estudiantesRiesgoPaginados(): RendimientoEstudianteItem[] {
    return this.rendimientoService.getPage(this.estudiantesRiesgo, this.currentPage, this.pageSize);
  }

  get desdeRegistro(): number {
    if (this.totalEstudiantesRiesgo === 0) {
      return 0;
    }
    return (this.currentPage - 1) * this.pageSize + 1;
  }

  get hastaRegistro(): number {
    return Math.min(this.currentPage * this.pageSize, this.totalEstudiantesRiesgo);
  }

  get pageNumbers(): number[] {
    return Array.from({ length: this.totalPages }, (_, index) => index + 1);
  }

  exportarCsv(): void {
    const csv = this.rendimientoService.buildCsv(this.estudiantesRiesgo);
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    this.downloadBlob(blob, `rendimiento_${this.codigoMateria || 'materia'}.csv`);
  }

  exportarPdf(): void {
    const html = this.rendimientoService.buildPdfHtml({
      title: 'Rendimiento — alumnos en riesgo',
      subtitle: `Materia NRC ${this.codigoMateria}`,
      rows: this.estudiantesRiesgo,
      summary: `${this.totalEstudiantesRiesgo} alumno(s) con promedio menor a 7.0`,
    });
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    this.downloadBlob(blob, `rendimiento_${this.codigoMateria || 'materia'}.html`);
  }

  irAPagina(page: number): void {
    this.currentPage = Math.min(Math.max(page, 1), this.totalPages);
  }

  paginaAnterior(): void {
    this.irAPagina(this.currentPage - 1);
  }

  paginaSiguiente(): void {
    this.irAPagina(this.currentPage + 1);
  }

  private downloadBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  }
}
