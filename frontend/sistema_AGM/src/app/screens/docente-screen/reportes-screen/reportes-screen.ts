import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { FacadeService } from '../../../services/facade.service';

interface PeriodoStat {
  periodo_nombre?: string;
  materia_nombre?: string;
  materia_id?: number;
  total_alumnos?: number;
  aprobados?: number;
  reprobados?: number;
  promedio_grupal?: number;
  porcentaje_asistencia?: number;
}

interface ChartBar {
  label: string;
  promedioPct: number;
  aprobacionPct: number;
}

@Component({
  selector: 'app-reportes-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './reportes-screen.html',
  styleUrl: './reportes-screen.scss',
})
export class ReportesScreen implements OnInit {
  historial: Array<{ documento: string; materia: string; fecha: string }> = [];

  materiasOpciones: Array<{ id: number; label: string }> = [];
  selectedMateriaId = 0;
  formato: 'pdf' | 'xlsx' = 'pdf';
  tipoReporte: 'calificaciones' | 'asistencias' = 'calificaciones';

  loading = false;
  loadingStats = true;
  errorMessage = '';

  promedioGeneral = '—';
  indiceAprobacion = '—';
  materiasActivas = 0;
  chartBars: ChartBar[] = [];
  periodos: PeriodoStat[] = [];
  periodoFiltro = '';

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    this.loadMaterias();
    this.loadEstadisticasDocente();
  }

  private loadMaterias(): void {
    const uid = this.facade.getUserId();
    if (!uid) {
      return;
    }
    this.facade.listMateriasDocente(uid, { limit: 200 }).subscribe({
      next: (body) => {
        const rows = this.facade.extractList<{
          id?: number;
          nrc?: string;
          nombre?: string;
        }>(body);
        this.materiasOpciones = rows
          .filter((m) => m.id)
          .map((m) => ({
            id: m.id as number,
            label: `${m.nombre ?? 'Materia'} (${m.nrc ?? ''})`,
          }));
        if (this.materiasOpciones.length && !this.selectedMateriaId) {
          this.selectedMateriaId = this.materiasOpciones[0].id;
        }
      },
    });
  }

  private loadEstadisticasDocente(): void {
    const docenteId = this.facade.getUserId();
    if (!docenteId) {
      this.loadingStats = false;
      return;
    }
    this.facade.getEstadisticasDocente(docenteId).subscribe({
      next: (body) => {
        this.loadingStats = false;
        const data = body?.data as { periodos?: PeriodoStat[] };
        this.periodos = data?.periodos ?? [];
        this.rebuildDashboard();
      },
      error: () => {
        this.loadingStats = false;
        this.periodos = [];
        this.rebuildDashboard();
      },
    });
  }

  get periodosUnicos(): string[] {
    const names = new Set(
      this.periodos.map((p) => p.periodo_nombre).filter((n): n is string => Boolean(n)),
    );
    return Array.from(names);
  }

  onPeriodoFiltroChange(event: Event): void {
    const select = event.target as HTMLSelectElement;
    this.periodoFiltro = select.value;
    this.rebuildDashboard();
  }

  private periodosFiltrados(): PeriodoStat[] {
    if (!this.periodoFiltro) {
      return this.periodos;
    }
    return this.periodos.filter((p) => p.periodo_nombre === this.periodoFiltro);
  }

  private rebuildDashboard(): void {
    const rows = this.periodosFiltrados();
    this.materiasActivas = rows.length;

    if (!rows.length) {
      this.promedioGeneral = '—';
      this.indiceAprobacion = '—';
      this.chartBars = [];
      return;
    }

    const promedios = rows.map((p) => p.promedio_grupal ?? 0);
    this.promedioGeneral = (promedios.reduce((a, b) => a + b, 0) / promedios.length).toFixed(2);

    let totalAlumnos = 0;
    let totalAprobados = 0;
    rows.forEach((p) => {
      totalAlumnos += p.total_alumnos ?? 0;
      totalAprobados += p.aprobados ?? 0;
    });
    this.indiceAprobacion =
      totalAlumnos > 0 ? `${((100 * totalAprobados) / totalAlumnos).toFixed(1)}%` : '—';

    const maxProm = Math.max(...promedios, 10);
    this.chartBars = rows.slice(0, 6).map((p) => {
      const prom = p.promedio_grupal ?? 0;
      const total = p.total_alumnos ?? 0;
      const aprob = p.aprobados ?? 0;
      const label = (p.materia_nombre ?? 'Materia').slice(0, 12);
      return {
        label,
        promedioPct: Math.round((prom / maxProm) * 100),
        aprobacionPct: total > 0 ? Math.round((aprob / total) * 100) : 0,
      };
    });
  }

  onMateriaChange(event: Event): void {
    const select = event.target as HTMLSelectElement;
    this.selectedMateriaId = Number(select.value);
  }

  setFormato(fmt: 'pdf' | 'xlsx'): void {
    this.formato = fmt;
  }

  setTipoReporte(tipo: 'calificaciones' | 'asistencias'): void {
    this.tipoReporte = tipo;
  }

  generarReporte(): void {
    if (!this.selectedMateriaId) {
      this.errorMessage = 'Seleccione una materia.';
      return;
    }
    this.errorMessage = '';
    this.loading = true;
    this.facade
      .downloadReporte(this.tipoReporte, this.selectedMateriaId, this.formato)
      .subscribe({
        next: (blob) => {
          this.loading = false;
          const ext = this.formato === 'pdf' ? 'pdf' : 'xlsx';
          const prefix = this.tipoReporte === 'asistencias' ? 'asistencias' : 'calificaciones';
          this.facade.triggerDownload(
            blob,
            `${prefix}_${this.selectedMateriaId}.${ext}`,
          );
          const label =
            this.materiasOpciones.find((m) => m.id === this.selectedMateriaId)?.label ?? '';
          this.historial = [
            {
              documento: `${prefix}.${ext}`,
              materia: label,
              fecha: new Date().toLocaleString('es-MX'),
            },
            ...this.historial,
          ].slice(0, 5);
        },
        error: () => {
          this.loading = false;
          this.errorMessage =
            'Error al generar el reporte. Verifique permisos, datos en MS-4/MS-5 y USE_MOCK_DATA=False.';
        },
      });
  }
}
