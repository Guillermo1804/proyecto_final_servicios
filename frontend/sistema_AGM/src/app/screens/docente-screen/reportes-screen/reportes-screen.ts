import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { ReportesDocenteService, ReporteAcademicoPeriodoItem, ReporteComparativaItem, ReporteExportacionItem, ReportePeriodoEscolarItem } from '../../../services/docente-services/reportes-docente.service';

@Component({
  selector: 'app-reportes-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './reportes-screen.html',
  styleUrl: './reportes-screen.scss'
})
export class ReportesScreen {

  historial: ReporteExportacionItem[] = [];
  historialAcademico: ReporteAcademicoPeriodoItem[] = [];
  materiasComparadas: ReporteComparativaItem[] = [];
  periodosEscolares: ReportePeriodoEscolarItem[] = [];

  constructor(private readonly reportesService: ReportesDocenteService) {
    this.historial = this.reportesService.getHistorial();
    this.historialAcademico = this.reportesService.getHistorialAcademico();
    this.materiasComparadas = this.reportesService.getMateriasComparadas();
    this.periodosEscolares = this.reportesService.getPeriodosEscolares();
  }

}