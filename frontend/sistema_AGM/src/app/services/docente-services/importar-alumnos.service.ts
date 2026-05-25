import { Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';

import { ImportarAlumnosPreviewDto } from '../../models/alumnos-api.model';
import { AlumnosService } from '../alumno-services/alumnos.service';

export interface ImportPreviewRow {
  matricula: string;
  nombre: string;
  correo: string;
  raw: Record<string, unknown>;
}

export interface ImportResult {
  success: boolean;
  imported?: number;
  actualizados?: number;
  errors?: string[];
}

@Injectable({ providedIn: 'root' })
export class ImportarAlumnosService {
  constructor(private alumnos: AlumnosService) {}

  previewFile(file: File): Observable<ImportPreviewRow[]> {
    return this.alumnos.importarPreview(file).pipe(map(mapPreviewToRows));
  }

  confirmar(rows: ImportPreviewRow[]): Observable<ImportResult> {
    const payload = rows.map((row) => row.raw);
    return this.alumnos.importarConfirmar(payload).pipe(
      map((data) => ({
        success: true,
        imported: data.creados,
        actualizados: data.actualizados,
      })),
    );
  }
}

function mapPreviewToRows(preview: ImportarAlumnosPreviewDto): ImportPreviewRow[] {
  return (preview.validas ?? []).map((row) => {
    const matricula = String(row['matricula'] ?? row['Matricula'] ?? '');
    const nombre = String(
      row['nombre_completo'] ??
        `${row['apellido'] ?? ''}, ${row['nombre'] ?? ''}`.replace(/^,\s*/, ''),
    ).trim();
    const correo = String(row['email'] ?? row['correo'] ?? '');
    return { matricula, nombre, correo, raw: row };
  });
}
