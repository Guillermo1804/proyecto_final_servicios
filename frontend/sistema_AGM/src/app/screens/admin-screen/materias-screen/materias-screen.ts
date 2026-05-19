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
  periodoId: number;
  nrc: string;
  seccion: string;
  clave: string;
  docenteNombre: string;
  docenteId: number | null;
  horario: string;
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
  editingId: number | null = null;
  editMateria: MateriaCard | null = null;

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
          periodo?: number;
          nrc?: string;
          clave?: string;
          nombre?: string;
          seccion?: string;
          docente_nombre?: string;
          docente_id?: number | null;
          horario?: string;
        }>(body);
        this.materias = rows.map((m) => ({
          id: m.id ?? 0,
          codigo: m.nrc || m.clave || '—',
          nombre: m.nombre ?? '—',
          prerequisito: m.seccion ? `Sección ${m.seccion}` : '—',
          facultad: m.docente_nombre || 'Sin docente',
          tipo: 'ingenieria',
          periodoId: m.periodo ?? 0,
          nrc: m.nrc ?? '',
          seccion: m.seccion ?? '01',
          clave: m.clave ?? m.nrc ?? '',
          docenteNombre: m.docente_nombre ?? '',
          docenteId: m.docente_id ?? null,
          horario: m.horario ?? '',
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
    this.editingId = null;
    this.editMateria = null;
    this.successMessage = '';
    this.errorMessage = '';
  }

  startEdit(materia: MateriaCard): void {
    this.showCreateForm = false;
    this.editingId = materia.id;
    this.editMateria = { ...materia };
    this.successMessage = '';
    this.errorMessage = '';
  }

  cancelEdit(): void {
    this.editingId = null;
    this.editMateria = null;
  }

  submitCreate(): void {
    if (!this.newMateria.periodo || !this.newMateria.nrc.trim() || !this.newMateria.nombre.trim()) {
      this.errorMessage = 'Periodo, NRC y nombre son obligatorios.';
      return;
    }
    this.saving = true;
    this.errorMessage = '';
    this.facade.createMateria(this.buildPayload(this.newMateria)).subscribe({
      next: () => {
        this.saving = false;
        this.successMessage = 'Materia creada correctamente.';
        this.showCreateForm = false;
        this.resetNewMateria();
        this.loadMaterias();
      },
      error: () => {
        this.saving = false;
        this.errorMessage = 'No se pudo crear la materia.';
      },
    });
  }

  submitEdit(): void {
    if (!this.editMateria?.id) {
      return;
    }
    this.saving = true;
    this.errorMessage = '';
    const m = this.editMateria;
    this.facade
      .updateMateria(m.id, {
        periodo: m.periodoId,
        nrc: m.nrc.trim(),
        nombre: m.nombre.trim(),
        seccion: m.seccion.trim() || '01',
        clave: m.clave.trim() || m.nrc.trim(),
        docente_nombre: m.docenteNombre.trim() || 'Por asignar',
        horario: m.horario.trim(),
        ...(m.docenteId ? { docente_id: m.docenteId } : {}),
      })
      .subscribe({
        next: () => {
          this.saving = false;
          this.successMessage = 'Materia actualizada.';
          this.cancelEdit();
          this.loadMaterias();
        },
        error: () => {
          this.saving = false;
          this.errorMessage = 'No se pudo actualizar la materia.';
        },
      });
  }

  deleteMateria(materia: MateriaCard): void {
    if (!confirm(`¿Eliminar la materia ${materia.nombre}?`)) {
      return;
    }
    this.saving = true;
    this.facade.deleteMateria(materia.id).subscribe({
      next: () => {
        this.saving = false;
        this.successMessage = 'Materia eliminada.';
        this.loadMaterias();
      },
      error: () => {
        this.saving = false;
        this.errorMessage = 'No se pudo eliminar (puede tener inscripciones).';
      },
    });
  }

  private buildPayload(source: typeof this.newMateria): Record<string, unknown> {
    const payload: Record<string, unknown> = {
      periodo: source.periodo,
      nrc: source.nrc.trim(),
      nombre: source.nombre.trim(),
      seccion: source.seccion.trim() || '01',
      clave: source.clave.trim() || source.nrc.trim(),
      docente_nombre: source.docente_nombre.trim() || 'Por asignar',
      horario: source.horario.trim(),
    };
    if (source.docente_id) {
      payload['docente_id'] = source.docente_id;
    }
    return payload;
  }

  private resetNewMateria(): void {
    this.newMateria.nrc = '';
    this.newMateria.nombre = '';
    this.newMateria.clave = '';
    this.newMateria.docente_nombre = '';
    this.newMateria.docente_id = null;
    this.newMateria.horario = '';
  }
}
