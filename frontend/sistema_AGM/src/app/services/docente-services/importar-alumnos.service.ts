import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, map, Observable, of } from 'rxjs';

import { environment } from '../../../environments/environment';

export interface ImportResult {
  success: boolean;
  imported?: number;
  errors?: string[];
}

export interface ImportStatus {
  pending: boolean;
  imported: number;
}

@Injectable({ providedIn: 'root' })
export class ImportarAlumnosService {

  private readonly apiPath = '/docente/importar-alumnos/';

  constructor(private http: HttpClient) {}

  uploadCsv(nrc: string, file: File): Observable<ImportResult> {
    const url = this.buildApiUrl(`${this.apiPath}${nrc}/upload/`);
    const fd = new FormData();
    fd.append('file', file, file.name);

    return this.http.post<ImportResult>(url, fd).pipe(
      catchError(() => of({ success: true, imported: 0 }))
    );
  }

  getStatus(nrc: string): Observable<ImportStatus> {
    const url = this.buildApiUrl(`${this.apiPath}${nrc}/status/`);
    return this.http.get<ImportStatus>(url).pipe(
      catchError(() => of({ pending: false, imported: 0 }))
    );
  }

  getTemplate(): Observable<Blob> {
    const url = this.buildApiUrl(`${this.apiPath}template/`);
    const headers = new HttpHeaders({ 'Accept': 'text/csv' });
    return this.http.get(url, { headers, responseType: 'blob' as 'json' }) as Observable<Blob>;
  }

  // Fallback local parser (optional) — returns simple counts, not used by default
  parseCsvLocally(file: File): Observable<ImportResult> {
    return new Observable<ImportResult>((subscriber) => {
      const reader = new FileReader();
      reader.onload = () => {
        const text = String(reader.result || '');
        const lines = text.split(/\r?\n/).filter((l) => l.trim());
        // naive: first line header
        const imported = Math.max(0, lines.length - 1);
        subscriber.next({ success: true, imported });
        subscriber.complete();
      };
      reader.onerror = (err) => {
        subscriber.next({ success: false, errors: [String(err)] });
        subscriber.complete();
      };
      reader.readAsText(file);
    });
  }

  private buildApiUrl(path: string): string {
    const baseUrl = environment.apiBaseUrl || environment.url_api || '';
    return `${baseUrl.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
  }

}
