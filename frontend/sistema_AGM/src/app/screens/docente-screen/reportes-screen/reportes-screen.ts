import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import {
  ReportesDocenteService,
  ReporteAcademicoPeriodoItem,
  ReporteComparativaItem,
  ReporteExportacionItem,
  ReporteMateriaOpcionItem,
  ReportePeriodoEscolarItem,
  ReportesDocenteResumen,
} from '../../../services/docente-services/reportes-docente.service';
import { ReporteDescargaFormato, ReporteDescargaTipo } from '../../../models/reportes-api.model';

@Component({
  selector: 'app-reportes-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './reportes-screen.html',
  styleUrl: './reportes-screen.scss',
})
export class ReportesScreen implements OnInit {
  isLoading = true;
  loadError = '';
  fuenteDatos: 'ms7' | 'fallback' | 'empty' = 'empty';

  historial: ReporteExportacionItem[] = [];
  historialAcademico: ReporteAcademicoPeriodoItem[] = [];
  historialAcademicoVista: ReporteAcademicoPeriodoItem[] = [];
  materiasComparadas: ReporteComparativaItem[] = [];
  periodosEscolares: ReportePeriodoEscolarItem[] = [];
  materiasOpciones: ReporteMateriaOpcionItem[] = [];
  resumen: ReportesDocenteResumen = {
    promedioGeneral: 0,
    indiceAprobacion: 0,
    alumnosAprobados: 0,
    alumnosEnRiesgo: 0,
    materiasActivas: 0,
  };
  insightObservacion = '';
  insightAccion = '';

  chartMaterias: Array<{ nombre: string; promedioPct: number; aprobacionPct: number }> = [];

  filtroPeriodo = '';
  filtroMateriaId: number | null = null;

  selectedMateriaId: number | null = null;
  tipoExport: ReporteDescargaTipo = 'calificaciones';
  exportFormat: ReporteDescargaFormato = 'pdf';
  exportLoading = false;
  exportError = '';

  constructor(private readonly reportesService: ReportesDocenteService) {}

  ngOnInit(): void {
    this.reportesService
      .loadReportes()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (data) => {
          this.historial = data.historial;
          this.historialAcademico = data.historialAcademico;
          this.materiasComparadas = data.materiasComparadas;
          this.periodosEscolares = data.periodosEscolares;
          this.materiasOpciones = data.materiasOpciones;
          this.resumen = data.resumen;
          this.insightObservacion = data.insightObservacion;
          this.insightAccion = data.insightAccion;
          this.fuenteDatos = data.fuente;
          this.selectedMateriaId = data.materiasOpciones[0]?.id ?? null;
          this.aplicarFiltros();
          this.loadError = '';
        },
        error: () => {
          this.loadError = 'No se pudieron cargar los reportes (MS-7).';
        },
      });
  }

  aplicarFiltros(): void {
    let vista = [...this.historialAcademico];
    if (this.filtroPeriodo) {
      vista = vista.filter((p) => p.periodo === this.filtroPeriodo);
    }
    if (this.filtroMateriaId != null) {
      vista = vista
        .map((p) => ({
          ...p,
          materias: p.materias.filter((m) => m.materiaId === this.filtroMateriaId),
        }))
        .filter((p) => p.materias.length > 0);
    }
    this.historialAcademicoVista = vista;
    this.chartMaterias = this.buildChart(vista);
  }

  exportar(formato: ReporteDescargaFormato): void {
    this.exportError = '';
    if (!this.selectedMateriaId) {
      this.exportError = 'Seleccione una materia para exportar.';
      return;
    }

    this.exportFormat = formato;
    this.exportLoading = true;
    this.reportesService
      .exportarReporte(this.tipoExport, this.selectedMateriaId, formato)
      .pipe(finalize(() => (this.exportLoading = false)))
      .subscribe({
        next: (blob) => {
          const materiaLabel =
            this.materiasOpciones.find((m) => m.id === this.selectedMateriaId)?.label ??
            `Materia ${this.selectedMateriaId}`;
          const nombreArchivo = `${this.tipoExport}_${this.selectedMateriaId}.${formato}`;
          this.downloadBlob(blob, nombreArchivo);
          const documento =
            this.tipoExport === 'calificaciones'
              ? `Acta calificaciones (${formato.toUpperCase()})`
              : `Reporte asistencias (${formato.toUpperCase()})`;
          const item: ReporteExportacionItem = {
            documento,
            materia: materiaLabel,
            fecha: new Date().toLocaleString('es-MX'),
          };
          this.reportesService.registrarExportacion(item);
          this.historial = this.reportesService.getHistorialExportaciones();
          this.exportError = '';
        },
        error: (err: Error) => {
          this.exportError = err.message || 'No se pudo generar el documento.';
        },
      });
  }

  fuenteEtiqueta(): string {
    if (this.fuenteDatos === 'ms7') {
      return 'MS-7 (estadísticas y exportación)';
    }
    if (this.fuenteDatos === 'fallback') {
      return 'MS-2/3/4 (MS-7 sin proyecciones)';
    }
    return 'Sin datos';
  }

  private buildChart(
    historial: ReporteAcademicoPeriodoItem[],
  ): Array<{ nombre: string; promedioPct: number; aprobacionPct: number }> {
    const activo = historial.find((p) => p.activo) ?? historial[0];
    if (!activo?.materias?.length) {
      return [];
    }
    return activo.materias.map((m) => ({
      nombre: m.nombre.length > 14 ? `${m.nombre.slice(0, 12)}…` : m.nombre,
      promedioPct: Math.min(100, Math.round((m.promedio / 10) * 100)),
      aprobacionPct: Math.min(100, m.aprobacion),
    }));
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
