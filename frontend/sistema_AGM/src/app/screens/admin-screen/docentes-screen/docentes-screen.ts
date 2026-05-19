import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAdmin } from '../../../partials/bottom-navbar-admin/bottom-navbar-admin';
import { FacadeService } from '../../../services/facade.service';

interface DocenteCard {
  nombre: string;
  id: string;
  usuarioId: number;
  facultad: string;
  estado: string;
  tipo: string;
}

@Component({
  selector: 'app-docentes-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, TopbarAdmin, BottomNavbarAdmin],
  templateUrl: './docentes-screen.html',
  styleUrl: './docentes-screen.scss',
})
export class DocentesScreen implements OnInit {
  docentes: DocenteCard[] = [];
  docentesFiltrados: DocenteCard[] = [];
  loading = true;
  errorMessage = '';
  successMessage = '';
  searchTerm = '';
  saving = false;

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    this.loadDocentes();
  }

  loadDocentes(): void {
    this.loading = true;
    this.errorMessage = '';
    this.facade.listDocentes({ limit: 100 }).subscribe({
      next: (body) => {
        this.loading = false;
        const rows = this.facade.extractList<{
          id?: number;
          nombre?: string;
          apellido?: string;
          departamento?: string;
          usuario_id?: number;
        }>(body);
        this.docentes = rows.map((d) => ({
          nombre: [d.nombre, d.apellido].filter(Boolean).join(' ') || '—',
          id: d.usuario_id ? String(d.usuario_id) : String(d.id ?? '—'),
          usuarioId: d.usuario_id ?? 0,
          facultad: d.departamento || 'AGM',
          estado: 'Activo',
          tipo: 'activo',
        }));
        this.applySearch();
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudieron cargar los docentes.';
      },
    });
  }

  applySearch(): void {
    const q = this.searchTerm.trim().toLowerCase();
    this.docentesFiltrados = q
      ? this.docentes.filter(
          (d) =>
            d.nombre.toLowerCase().includes(q) ||
            d.id.toLowerCase().includes(q) ||
            d.facultad.toLowerCase().includes(q),
        )
      : [...this.docentes];
  }

  onSearchChange(): void {
    this.applySearch();
  }

  onImportPdf(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) {
      return;
    }
    this.saving = true;
    this.errorMessage = '';
    this.facade.importDocentesPdf(file).subscribe({
      next: (body) => {
        this.saving = false;
        const data = body?.data as { creados?: number; omitidos?: number; errores?: number } | undefined;
        this.successMessage = `Importación: ${data?.creados ?? 0} creados, ${data?.omitidos ?? 0} omitidos.`;
        input.value = '';
        this.loadDocentes();
      },
      error: () => {
        this.saving = false;
        this.errorMessage = 'Error al importar el PDF de docentes.';
        input.value = '';
      },
    });
  }

  openImportPdf(): void {
    const el = document.getElementById('import-docentes-pdf') as HTMLInputElement | null;
    el?.click();
  }

  resetPasswordDocente(docente: DocenteCard): void {
    if (!docente.usuarioId) {
      this.errorMessage = 'Este docente no tiene usuario_id en MS-1.';
      return;
    }
    if (!confirm(`¿Enviar enlace de restablecimiento a ${docente.nombre}?`)) {
      return;
    }
    this.saving = true;
    this.facade.resetUsuarioPassword(docente.usuarioId).subscribe({
      next: () => {
        this.saving = false;
        this.successMessage = 'Se envió el correo de restablecimiento.';
      },
      error: () => {
        this.saving = false;
        this.errorMessage = 'No se pudo solicitar el reset de contraseña.';
      },
    });
  }
}
