import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import {
  ImportPreviewRow,
  ImportarAlumnosService,
} from '../../../services/docente-services/importar-alumnos.service';
import { AlumnosService } from '../../../services/alumno-services/alumnos.service';

@Component({
  selector: 'app-importar-alumnos-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './importar-alumnos-screen.html',
  styleUrl: './importar-alumnos-screen.scss',
})
export class ImportarAlumnosScreen {
  codigoMateria = '';
  alumnos: ImportPreviewRow[] = [];
  previewRows: ImportPreviewRow[] = [];
  isLoading = false;
  errorMessage = '';
  successMessage = '';

  constructor(
    private route: ActivatedRoute,
    private importarService: ImportarAlumnosService,
  ) {
    this.codigoMateria = this.route.snapshot.paramMap.get('id') ?? '';
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) {
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.importarService.previewFile(file).subscribe({
      next: (rows) => {
        this.previewRows = rows;
        this.alumnos = rows;
        this.isLoading = false;
      },
      error: (err) => {
        this.errorMessage = AlumnosService.extractError(
          err,
          'No se pudo leer el archivo de alumnos.',
        );
        this.isLoading = false;
      },
    });
    input.value = '';
  }

  confirmarImportacion(): void {
    if (!this.previewRows.length) {
      alert('Primero carga un archivo valido.');
      return;
    }

    this.isLoading = true;
    this.importarService.confirmar(this.previewRows).subscribe({
      next: (result) => {
        this.successMessage = `Importacion OK. Creados: ${result.imported ?? 0}, actualizados: ${result.actualizados ?? 0}`;
        this.isLoading = false;
      },
      error: (err) => {
        this.errorMessage = AlumnosService.extractError(err, 'No se pudo confirmar la importacion.');
        this.isLoading = false;
      },
    });
  }
}
