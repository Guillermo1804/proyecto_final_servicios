import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { FacadeService } from '../../../services/facade.service';

interface AlumnoPreviewRow {
  matricula: string;
  nombre: string;
  correo: string;
  raw: Record<string, unknown>;
}

@Component({
  selector: 'app-importar-alumnos-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './importar-alumnos-screen.html',
  styleUrl: './importar-alumnos-screen.scss',
})
export class ImportarAlumnosScreen {
  codigoMateria = '';
  materiaId = 0;
  alumnos: AlumnoPreviewRow[] = [];
  previewRows: Record<string, unknown>[] = [];
  totalValidas = 0;
  totalErrores = 0;
  previewReady = false;
  loading = false;
  saving = false;
  errorMessage = '';
  successMessage = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private facade: FacadeService,
  ) {
    this.codigoMateria = this.route.snapshot.paramMap.get('id') ?? '';
    const id = Number(this.codigoMateria);
    this.materiaId = Number.isFinite(id) ? id : 0;
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) {
      return;
    }
    this.loading = true;
    this.errorMessage = '';
    this.previewReady = false;
    this.facade.previewImportAlumnos(file).subscribe({
      next: (body) => {
        this.loading = false;
        const data = body?.data as {
          validas?: Record<string, unknown>[];
          total_validas?: number;
          total_errores?: number;
        };
        this.previewRows = data?.validas ?? [];
        this.totalValidas = data?.total_validas ?? this.previewRows.length;
        this.totalErrores = data?.total_errores ?? 0;
        this.alumnos = this.previewRows.map((row) => ({
          matricula: String(row['matricula'] ?? '—'),
          nombre: [row['nombre'], row['apellido']].filter(Boolean).join(' '),
          correo: String(row['email'] ?? '—'),
          raw: row,
        }));
        this.previewReady = this.alumnos.length > 0;
        input.value = '';
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudo validar el archivo.';
        input.value = '';
      },
    });
  }

  confirmImport(): void {
    if (!this.previewRows.length) {
      return;
    }
    this.saving = true;
    this.errorMessage = '';
    const payload = this.previewRows.map((row) => ({ ...row }));
    this.facade.confirmImportAlumnos(payload, this.materiaId || undefined).subscribe({
      next: (body) => {
        this.saving = false;
        const data = body?.data as { creados?: number; inscripciones?: number } | undefined;
        this.successMessage = `Importados: ${data?.creados ?? 0} alumnos.`;
        if (this.materiaId) {
          void this.router.navigate(['/docente/materias', this.codigoMateria]);
        }
      },
      error: () => {
        this.saving = false;
        this.errorMessage = 'Error al confirmar la importación.';
      },
    });
  }

  openFilePicker(): void {
    const el = document.getElementById('import-alumnos-file') as HTMLInputElement | null;
    el?.click();
  }
}
