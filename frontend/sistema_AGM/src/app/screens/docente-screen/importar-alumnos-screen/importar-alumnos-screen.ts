import { CommonModule } from '@angular/common';
import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { AlumnoImportPreviewFilaDto } from '../../../models/alumnos-api.model';
import { AlumnosService } from '../../../services/alumno-services/alumnos.service';
import {
  ImportarAlumnosPdfResult,
  ImportarAlumnosPreview,
  ImportarAlumnosService,
} from '../../../services/docente-services/importar-alumnos.service';
import { MateriasDocenteService } from '../../../services/docente-services/materias-docente.service';

const MAX_PDF_BYTES = 5 * 1024 * 1024;
const PREVIEW_PAGE_SIZE = 5;

@Component({
  selector: 'app-importar-alumnos-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente, RouterLink],
  templateUrl: './importar-alumnos-screen.html',
  styleUrl: './importar-alumnos-screen.scss',
})
export class ImportarAlumnosScreen implements OnInit {
  @ViewChild('fileInput') fileInput?: ElementRef<HTMLInputElement>;

  codigoMateria = '';
  materiaId: number | null = null;
  materiaNombre = '';
  resolvingMateria = true;

  selectedFile: File | null = null;
  isDragOver = false;
  isPreviewLoading = false;
  isConfirmLoading = false;
  errorMessage = '';
  successMessage = '';
  preview: ImportarAlumnosPreview | null = null;
  lastResult: ImportarAlumnosPdfResult | null = null;
  previewPage = 1;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private importarService: ImportarAlumnosService,
    private materiasDocente: MateriasDocenteService,
  ) {
    this.codigoMateria = this.route.snapshot.paramMap.get('id') ?? '';
  }

  ngOnInit(): void {
    const state = history.state as { materiaId?: number; materiaNombre?: string } | null;
    if (state?.materiaId) {
      this.materiaId = Number(state.materiaId);
      this.resolvingMateria = false;
    }
    if (state?.materiaNombre) {
      this.materiaNombre = state.materiaNombre;
    }

    if (!this.codigoMateria) {
      this.resolvingMateria = false;
      this.errorMessage = 'No se encontro el NRC de la materia en la ruta.';
      return;
    }

    this.materiasDocente
      .findMateriaByNrcForImport(this.codigoMateria)
      .pipe(finalize(() => (this.resolvingMateria = false)))
      .subscribe({
        next: (m) => {
          if (m) {
            this.materiaId = m.id;
            this.materiaNombre = m.materia;
          } else if (!this.materiaId) {
            this.errorMessage =
              'No se encontro la materia con este NRC en el periodo activo. Revisa MS-2 (Periodos).';
          }
        },
        error: () => {
          if (!this.materiaId) {
            this.errorMessage = 'No se pudo cargar la materia. Intenta de nuevo.';
          }
        },
      });
  }

  get isLoading(): boolean {
    return this.isPreviewLoading || this.isConfirmLoading;
  }

  get canPickFile(): boolean {
    return !!this.materiaId && !this.isLoading && !this.resolvingMateria;
  }

  get canConfirm(): boolean {
    return (
      this.canPickFile &&
      !!this.preview?.filas?.length &&
      !this.hasBlockingAdvertencias &&
      !this.isPreviewLoading
    );
  }

  get previewFilas(): AlumnoImportPreviewFilaDto[] {
    return this.preview?.filas ?? [];
  }

  get previewTotalPages(): number {
    const total = this.previewFilas.length;
    return total > 0 ? Math.ceil(total / PREVIEW_PAGE_SIZE) : 1;
  }

  get previewPageFilas(): AlumnoImportPreviewFilaDto[] {
    const start = (this.previewPage - 1) * PREVIEW_PAGE_SIZE;
    return this.previewFilas.slice(start, start + PREVIEW_PAGE_SIZE);
  }

  get hasBlockingAdvertencias(): boolean {
    return this.advertencias.some((msg) =>
      /no coincide con la materia/i.test(msg),
    );
  }

  get advertencias(): string[] {
    const detalle = this.preview?.advertencias ?? [];
    return detalle
      .map((item) => String(item?.error ?? ''))
      .filter((msg) => msg.length > 0);
  }

  get detalleErrores(): string[] {
    const detalle = this.lastResult?.detalle_errores ?? [];
    return detalle
      .map((item) => String(item?.error ?? ''))
      .filter((msg) => msg.length > 0);
  }

  volverUrl(): string[] {
    return ['/docente/materias', this.codigoMateria];
  }

  onDropZoneClick(): void {
    if (!this.canPickFile) {
      return;
    }
    this.fileInput?.nativeElement.click();
  }

  onDropZoneKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      this.onDropZoneClick();
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    if (this.canPickFile) {
      this.isDragOver = true;
    }
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;
    if (!this.canPickFile) {
      return;
    }
    const file = event.dataTransfer?.files?.[0];
    if (file) {
      this.setSelectedFile(file);
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) {
      this.setSelectedFile(file);
    }
    input.value = '';
  }

  clearFile(): void {
    this.selectedFile = null;
    this.preview = null;
    this.previewPage = 1;
    this.lastResult = null;
    this.successMessage = '';
    if (!this.resolvingMateria && this.materiaId) {
      this.errorMessage = '';
    }
  }

  confirmarImportacion(): void {
    if (!this.canConfirm || !this.materiaId || !this.preview) {
      return;
    }
    this.ejecutarConfirmacion(this.materiaId, this.preview);
  }

  prevPreviewPage(): void {
    if (this.previewPage > 1) {
      this.previewPage -= 1;
    }
  }

  nextPreviewPage(): void {
    if (this.previewPage < this.previewTotalPages) {
      this.previewPage += 1;
    }
  }

  accionLabel(accion: string): string {
    return accion === 'nuevo' ? 'Nuevo' : 'Actualizar';
  }

  inscripcionLabel(inscripcion: string): string {
    if (inscripcion === 'ya_inscrito') {
      return 'Ya inscrito';
    }
    if (inscripcion === 'reactivar') {
      return 'Reactivar';
    }
    return 'Inscribir';
  }

  private setSelectedFile(file: File): void {
    const validationError = this.validatePdf(file);
    if (validationError) {
      this.errorMessage = validationError;
      this.selectedFile = null;
      this.preview = null;
      return;
    }

    this.selectedFile = file;
    this.errorMessage = '';
    this.successMessage = '';
    this.lastResult = null;
    this.preview = null;
    this.previewPage = 1;

    if (this.materiaId) {
      this.cargarVistaPrevia(this.materiaId, file);
    }
  }

  private validatePdf(file: File): string | null {
    const name = file.name.toLowerCase();
    if (!name.endsWith('.pdf') && file.type !== 'application/pdf') {
      return 'Solo se aceptan archivos PDF (lista de clase BUAP).';
    }
    if (file.size > MAX_PDF_BYTES) {
      return 'El PDF supera el limite de 5 MB.';
    }
    if (file.size === 0) {
      return 'El archivo esta vacio.';
    }
    return null;
  }

  private cargarVistaPrevia(materiaId: number, file: File): void {
    this.isPreviewLoading = true;
    this.errorMessage = '';

    this.importarService
      .previewPdf(materiaId, file)
      .pipe(finalize(() => (this.isPreviewLoading = false)))
      .subscribe({
        next: (preview) => {
          this.preview = preview;
          const total = preview.resumen?.total ?? preview.filas?.length ?? 0;
          if (total === 0) {
            this.errorMessage =
              'El PDF no contiene alumnos validos. Exporta la lista desde Servicios Web (Ctrl+P).';
          } else if (this.hasBlockingAdvertencias) {
            this.errorMessage =
              'El NRC del PDF no coincide con esta materia. Corrige el archivo antes de confirmar.';
          } else {
            this.successMessage = `Vista previa: ${total} alumno(s) listos para importar o actualizar.`;
          }
        },
        error: (err) => {
          this.preview = null;
          this.errorMessage = AlumnosService.extractError(
            err,
            'No se pudo generar la vista previa del PDF.',
          );
        },
      });
  }

  private ejecutarConfirmacion(materiaId: number, preview: ImportarAlumnosPreview): void {
    this.isConfirmLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.importarService
      .confirmarImportacion(materiaId, preview)
      .pipe(finalize(() => (this.isConfirmLoading = false)))
      .subscribe({
        next: (result) => {
          this.lastResult = result;
          const creados = result.creados ?? 0;
          const actualizados = result.actualizados ?? 0;
          const inscritos = result.inscritos ?? 0;
          this.successMessage = `Importacion completada: ${creados} creado(s), ${actualizados} actualizado(s), ${inscritos} inscripcion(es).`;
          if (inscritos > 0 || creados > 0 || actualizados > 0) {
            setTimeout(() => {
              void this.router.navigate(this.volverUrl());
            }, 2500);
          }
        },
        error: (err) => {
          this.errorMessage = AlumnosService.extractError(
            err,
            'No se pudo confirmar la importacion.',
          );
        },
      });
  }
}
