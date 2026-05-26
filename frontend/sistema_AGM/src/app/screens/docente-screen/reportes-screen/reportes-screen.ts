import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
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

@Component({
  selector: 'app-reportes-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './reportes-screen.html',
  styleUrl: './reportes-screen.scss',
})
export class ReportesScreen implements OnInit {
  isLoading = true;
  loadError = '';

  historial: ReporteExportacionItem[] = [];
  historialAcademico: ReporteAcademicoPeriodoItem[] = [];
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
          this.chartMaterias = this.buildChart(data.historialAcademico);
          this.loadError = '';
        },
        error: () => {
          this.loadError = 'No se pudieron cargar los reportes (MS-2, MS-3, MS-4).';
        },
      });
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
}
