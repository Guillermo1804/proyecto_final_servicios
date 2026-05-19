import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAdmin } from '../../../partials/bottom-navbar-admin/bottom-navbar-admin';
import { FacadeService } from '../../../services/facade.service';

interface PeriodoCard {
  id: number;
  nombre: string;
  estado: string;
  tipo: string;
  fechaInicio: string;
  icono: string;
  activo: boolean;
}

@Component({
  selector: 'app-periodos-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, TopbarAdmin, BottomNavbarAdmin],
  templateUrl: './periodos-screen.html',
  styleUrl: './periodos-screen.scss',
})
export class PeriodosScreen implements OnInit {
  periodos: PeriodoCard[] = [];
  periodosFiltrados: PeriodoCard[] = [];
  loading = true;
  errorMessage = '';
  successMessage = '';
  periodoActualNombre = '—';
  totalPeriodos = 0;
  searchTerm = '';
  showCreateForm = false;
  saving = false;
  importPeriodoId: number | null = null;

  newPeriodo = {
    nombre: '',
    fecha_inicio: '',
    fecha_fin: '',
  };

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    this.loadPeriodoActivo();
    this.loadPeriodos();
  }

  loadPeriodoActivo(): void {
    this.facade.getPeriodoActivo().subscribe({
      next: (activo) => {
        const p = activo?.data as { nombre?: string } | undefined;
        if (p?.nombre) {
          this.periodoActualNombre = p.nombre;
        }
      },
    });
  }

  loadPeriodos(): void {
    this.loading = true;
    this.errorMessage = '';
    this.facade.listPeriodos().subscribe({
      next: (body) => {
        this.loading = false;
        const rows = this.facade.extractList<{
          id?: number;
          nombre?: string;
          activo?: boolean;
          fecha_inicio?: string;
        }>(body);
        this.totalPeriodos = rows.length;
        this.periodos = rows.map((p) => ({
          id: p.id ?? 0,
          nombre: p.nombre ?? '—',
          estado: p.activo ? 'Activo' : 'Cerrado',
          tipo: p.activo ? 'activo' : 'cerrado',
          fechaInicio: p.fecha_inicio
            ? new Date(p.fecha_inicio).toLocaleDateString('es-MX')
            : '—',
          icono: p.activo ? 'azul' : 'gris',
          activo: !!p.activo,
        }));
        this.applySearch();
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudieron cargar los periodos.';
      },
    });
  }

  applySearch(): void {
    const q = this.searchTerm.trim().toLowerCase();
    this.periodosFiltrados = q
      ? this.periodos.filter((p) => p.nombre.toLowerCase().includes(q))
      : [...this.periodos];
  }

  onSearchChange(): void {
    this.applySearch();
  }

  toggleCreateForm(): void {
    this.showCreateForm = !this.showCreateForm;
    this.successMessage = '';
    this.errorMessage = '';
  }

  submitCreate(): void {
    if (!this.newPeriodo.nombre || !this.newPeriodo.fecha_inicio || !this.newPeriodo.fecha_fin) {
      this.errorMessage = 'Complete nombre y fechas del periodo.';
      return;
    }
    this.saving = true;
    this.errorMessage = '';
    this.facade.createPeriodo({ ...this.newPeriodo }).subscribe({
      next: () => {
        this.saving = false;
        this.showCreateForm = false;
        this.successMessage = 'Periodo creado correctamente.';
        this.newPeriodo = { nombre: '', fecha_inicio: '', fecha_fin: '' };
        this.loadPeriodos();
      },
      error: () => {
        this.saving = false;
        this.errorMessage = 'No se pudo crear el periodo.';
      },
    });
  }

  activar(periodo: PeriodoCard): void {
    if (periodo.activo || !periodo.id) {
      return;
    }
    this.saving = true;
    this.errorMessage = '';
    this.facade.activarPeriodo(periodo.id).subscribe({
      next: () => {
        this.saving = false;
        this.successMessage = `"${periodo.nombre}" activado.`;
        this.loadPeriodoActivo();
        this.loadPeriodos();
      },
      error: () => {
        this.saving = false;
        this.errorMessage = 'No se pudo activar el periodo.';
      },
    });
  }

  onImportFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    const periodoId = this.importPeriodoId;
    if (!file || !periodoId) {
      return;
    }
    this.saving = true;
    this.errorMessage = '';
    this.facade.importarMateriasPdf(periodoId, file).subscribe({
      next: (body) => {
        this.saving = false;
        const data = body?.data as { importadas?: number; fallidas?: number } | undefined;
        const imp = data?.importadas ?? 0;
        const fall = data?.fallidas ?? 0;
        this.successMessage = `Importación: ${imp} materias, ${fall} fallidas.`;
        input.value = '';
        this.importPeriodoId = null;
      },
      error: () => {
        this.saving = false;
        this.errorMessage = 'Error al importar el PDF.';
        input.value = '';
      },
    });
  }

  openImport(periodoId: number): void {
    this.importPeriodoId = periodoId;
    const el = document.getElementById('import-pdf-input') as HTMLInputElement | null;
    el?.click();
  }
}
