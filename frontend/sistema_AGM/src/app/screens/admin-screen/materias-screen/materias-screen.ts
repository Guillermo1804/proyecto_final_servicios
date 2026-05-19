import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAdmin } from '../../../partials/bottom-navbar-admin/bottom-navbar-admin';
import { FacadeService } from '../../../services/facade.service';

interface MateriaCard {
  id: number;
  codigo: string;
  nombre: string;
  prerequisito: string;
  facultad: string;
  tipo: string;
}

interface PeriodoOption {
  id: number;
  nombre: string;
}

@Component({
  selector: 'app-materias-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, TopbarAdmin, BottomNavbarAdmin],
  templateUrl: './materias-screen.html',
  styleUrl: './materias-screen.scss',
})
export class MateriasScreen implements OnInit {
  materias: MateriaCard[] = [];
  materiasFiltradas: MateriaCard[] = [];
  periodos: PeriodoOption[] = [];
  loading = true;
  saving = false;
  errorMessage = '';
  successMessage = '';
  searchTerm = '';
  selectedPeriodoId: number | null = null;
  showCreateForm = false;

  newMateria = {
    periodo: 0,
    nrc: '',
    nombre: '',
    seccion: '01',
    clave: '',
    docente_nombre: '',
    docente_id: null as number | null,
    horario: '',
  };

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    this.loadPeriodos();
    this.loadMaterias();
  }

  loadPeriodos(): void {
    this.facade.listPeriodos().subscribe({
      next: (body) => {
        const rows = this.facade.extractList<{ id?: number; nombre?: string }>(body);
        this.periodos = rows
          .filter((p) => p.id)
          .map((p) => ({ id: p.id as number, nombre: p.nombre ?? `Periodo ${p.id}` }));
        if (this.periodos.length && !this.newMateria.periodo) {
          this.newMateria.periodo = this.periodos[0].id;
        }
      },
    });
  }

  loadMaterias(): void {
    this.loading = true;
    this.errorMessage = '';
    const query: Record<string, string | number> = { limit: 200 };
    if (this.selectedPeriodoId) {
      query['periodo_id'] = this.selectedPeriodoId;
    }
    this.facade.listMaterias(query).subscribe({
      next: (body) => {
        this.loading = false;
        const rows = this.facade.extractList<{
          id?: number;
          nrc?: string;
          clave?: string;
          nombre?: string;
          seccion?: string;
          docente_nombre?: string;
        }>(body);
        this.materias = rows.map((m) => ({
          id: m.id ?? 0,
          codigo: m.nrc || m.clave || '—',
          nombre: m.nombre ?? '—',
          prerequisito: m.seccion ? `Sección ${m.seccion}` : '—',
          facultad: m.docente_nombre || 'Sin docente',
          tipo: 'ingenieria',
        }));
        this.applySearch();
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudieron cargar las materias.';
      },
    });
  }

  applySearch(): void {
    const q = this.searchTerm.trim().toLowerCase();
    this.materiasFiltradas = q
      ? this.materias.filter(
          (m) =>
            m.codigo.toLowerCase().includes(q) || m.nombre.toLowerCase().includes(q),
        )
      : [...this.materias];
  }

  onSearchChange(): void {
    this.applySearch();
  }

  onPeriodoFilterChange(): void {
    this.loadMaterias();
  }

  toggleCreateForm(): void {
    this.showCreateForm = !this.showCreateForm;
    this.successMessage = '';
    this.errorMessage = '';
  }

  submitCreate(): void {
    if (!this.newMateria.periodo || !this.newMateria.nrc.trim() || !this.newMateria.nombre.trim()) {
      this.errorMessage = 'Periodo, NRC y nombre son obligatorios.';
      return;
    }
    this.saving = true;
    this.errorMessage = '';
    const payload: Record<string, unknown> = {
      periodo: this.newMateria.periodo,
      nrc: this.newMateria.nrc.trim(),
      nombre: this.newMateria.nombre.trim(),
      seccion: this.newMateria.seccion.trim() || '01',
      clave: this.newMateria.clave.trim() || this.newMateria.nrc.trim(),
      docente_nombre: this.newMateria.docente_nombre.trim() || 'Por asignar',
      horario: this.newMateria.horario.trim(),
    };
    if (this.newMateria.docente_id) {
      payload['docente_id'] = this.newMateria.docente_id;
    }
    this.facade.createMateria(payload).subscribe({
      next: () => {
        this.saving = false;
        this.successMessage = 'Materia creada correctamente.';
        this.showCreateForm = false;
        this.newMateria.nrc = '';
        this.newMateria.nombre = '';
        this.newMateria.clave = '';
        this.newMateria.docente_nombre = '';
        this.newMateria.docente_id = null;
        this.newMateria.horario = '';
        this.loadMaterias();
      },
      error: () => {
        this.saving = false;
        this.errorMessage = 'No se pudo crear la materia.';
      },
    });
  }
}
