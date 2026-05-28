import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ImportarAlumnosPreviewDto,
  ImportarAlumnosPdfResultDto,
} from '../../models/alumnos-api.model';
import { AlumnosService } from '../alumno-services/alumnos.service';

export type ImportarAlumnosPdfResult = ImportarAlumnosPdfResultDto;
export type ImportarAlumnosPreview = ImportarAlumnosPreviewDto;

@Injectable({ providedIn: 'root' })
export class ImportarAlumnosService {
  constructor(private alumnos: AlumnosService) {}

  previewPdf(materiaId: number, file: File): Observable<ImportarAlumnosPreview> {
    return this.alumnos.previewImportarAlumnosPdf(materiaId, file);
  }

  confirmarImportacion(
    materiaId: number,
    preview: ImportarAlumnosPreview,
  ): Observable<ImportarAlumnosPdfResult> {
    return this.alumnos.confirmarImportarAlumnos(materiaId, preview.filas ?? []);
  }

  importarPdf(materiaId: number, file: File): Observable<ImportarAlumnosPdfResult> {
    return this.alumnos.importarAlumnosPdf(materiaId, file);
  }
}
