import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { RendimientoDocenteService, RendimientoEstudianteItem } from '../../../services/docente-services/rendimiento-docente.service';

@Component({
  selector: 'app-rendimiento-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './rendimiento-screen.html',
  styleUrl: './rendimiento-screen.scss'
})
export class RendimientoScreen {

  codigoMateria = '';
  estudiantesRiesgo: RendimientoEstudianteItem[] = [];
  totalEstudiantesRiesgo = 0;
  currentPage = 1;
  pageSize = 2;
  totalPages = 1;

  constructor(
    private route: ActivatedRoute,
    private readonly rendimientoService: RendimientoDocenteService
  ) {
    this.codigoMateria = this.route.snapshot.paramMap.get('id') ?? '';
    this.estudiantesRiesgo = this.rendimientoService.getEstudiantesRiesgo();
    this.totalEstudiantesRiesgo = this.estudiantesRiesgo.length;
    this.totalPages = this.rendimientoService.getTotalPages(this.totalEstudiantesRiesgo, this.pageSize);
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
      title: 'Reporte de Rendimiento Académico',
      subtitle: 'Alumnos en riesgo académico y seguimiento de desempeño.',
      rows: this.estudiantesRiesgo,
      summary: `Materia: ${this.codigoMateria || 'Sin código'} | Total de alumnos en riesgo: ${this.totalEstudiantesRiesgo}`
    });

    const printWindow = window.open('', '_blank', 'width=980,height=720');

    if (!printWindow) {
      alert('No se pudo abrir la vista de impresión para generar el PDF.');
      return;
    }

    printWindow.document.open();
    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
    }, 250);
  }

  cambiarPagina(pagina: number): void {
    if (pagina < 1 || pagina > this.totalPages) {
      return;
    }

    this.currentPage = pagina;
  }

  paginaAnterior(): void {
    this.cambiarPagina(this.currentPage - 1);
  }

  paginaSiguiente(): void {
    this.cambiarPagina(this.currentPage + 1);
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