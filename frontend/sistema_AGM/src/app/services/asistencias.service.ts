import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, catchError, throwError } from 'rxjs';

import {
  ConfirmarSesionResponse,
  IniciarSesionResponse,
  QrGenerateResponse,
  RegistrarAsistenciaResponse,
  RegistroAsistenciaApiDto,
  SesionActivaResponse,
  SesionesHistorialResponse,
  SesionAsistenciaApiDto,
  StatsAlumnoMateriaResponse,
  StatsSesionResponse,
} from '../models/asistencias-api.model';
import { buildApiUrl } from './tools/agm-api.helpers';

@Injectable({ providedIn: 'root' })
export class AsistenciasService {
  constructor(private http: HttpClient) {}

  iniciarSesion(materiaId: number, docenteId: number): Observable<IniciarSesionResponse> {
    return this.http
      .post<IniciarSesionResponse>(buildApiUrl('sesiones/iniciar/'), {
        materia_id: materiaId,
        docente_id: docenteId,
      })
      .pipe(catchError((err) => this.fail(err, 'No se pudo iniciar la sesión.')));
  }

  obtenerSesionActiva(materiaId: number): Observable<SesionActivaResponse> {
    const params = new HttpParams({ fromObject: { materia_id: String(materiaId) } });
    return this.http
      .get<SesionActivaResponse>(buildApiUrl('sesiones/activa/'), { params })
      .pipe(catchError((err) => this.fail(err, 'No se pudo consultar la sesión activa.')));
  }

  obtenerSesionPendiente(materiaId: number): Observable<SesionActivaResponse> {
    const params = new HttpParams({ fromObject: { materia_id: String(materiaId) } });
    return this.http
      .get<SesionActivaResponse>(buildApiUrl('sesiones/pendiente/'), { params })
      .pipe(catchError((err) => this.fail(err, 'No se pudo consultar la sesión pendiente.')));
  }

  cerrarSesion(sesionId: number): Observable<ConfirmarSesionResponse> {
    return this.http
      .delete<ConfirmarSesionResponse>(buildApiUrl(`sesiones/${sesionId}/cerrar/`))
      .pipe(catchError((err) => this.fail(err, 'No se pudo cerrar la sesión.')));
  }

  confirmarSesion(sesionId: number): Observable<ConfirmarSesionResponse> {
    return this.http
      .post<ConfirmarSesionResponse>(buildApiUrl(`sesiones/${sesionId}/confirmar/`), {})
      .pipe(catchError((err) => this.fail(err, 'No se pudo confirmar la lista.')));
  }

  solicitarNuevaLista(sesionId: number): Observable<ConfirmarSesionResponse> {
    return this.http
      .post<ConfirmarSesionResponse>(buildApiUrl(`sesiones/${sesionId}/solicitar-nueva/`), {})
      .pipe(catchError((err) => this.fail(err, 'No se pudo solicitar una nueva lista.')));
  }

  statsSesion(sesionId: number): Observable<StatsSesionResponse> {
    return this.http
      .get<StatsSesionResponse>(buildApiUrl(`sesiones/${sesionId}/stats/`))
      .pipe(catchError((err) => this.fail(err, 'No se pudieron cargar estadísticas.')));
  }

  statsAlumnoMateria(alumnoId: number, materiaId: number): Observable<StatsAlumnoMateriaResponse> {
    const params = new HttpParams({
      fromObject: {
        alumno_id: String(alumnoId),
        materia_id: String(materiaId),
      },
    });
    return this.http
      .get<StatsAlumnoMateriaResponse>(buildApiUrl('registros/stats_alumno_materia/'), { params })
      .pipe(catchError((err) => this.fail(err, 'No se pudieron cargar estadísticas de asistencia.')));
  }

  registrarAsistencia(encodedPayload: string): Observable<RegistrarAsistenciaResponse> {
    return this.http
      .post<RegistrarAsistenciaResponse>(buildApiUrl('asistencias/registrar/'), {
        encoded_payload: encodedPayload.trim(),
      })
      .pipe(catchError((err) => this.fail(err, 'QR no válido o sesión inactiva.')));
  }

  listarHistorialSesiones(
    materiaId: number,
    dias = 30,
    limit = 30,
  ): Observable<SesionesHistorialResponse> {
    const params = new HttpParams({
      fromObject: {
        materia_id: String(materiaId),
        dias: String(dias),
        limit: String(limit),
      },
    });
    return this.http
      .get<SesionesHistorialResponse>(buildApiUrl('sesiones/historial/'), { params })
      .pipe(catchError((err) => this.fail(err, 'No se pudo cargar el historial de pases.')));
  }

  listarRegistrosPorMateriaHoy(materiaId: number): Observable<RegistroAsistenciaApiDto[]> {
    const params = new HttpParams({ fromObject: { materia_id: String(materiaId) } });
    return this.http
      .get<RegistroAsistenciaApiDto[]>(buildApiUrl('registros/por_materia_hoy/'), { params })
      .pipe(catchError((err) => this.fail(err, 'No se pudo cargar el pase de lista de hoy.')));
  }

  descargarReporteAsistencias(materiaId: number, formato: 'pdf' | 'xlsx' = 'pdf'): Observable<Blob> {
    const params = new HttpParams({ fromObject: { formato } });
    return this.http.get(buildApiUrl(`reportes/asistencias/${materiaId}`), {
      params,
      responseType: 'blob',
    });
  }

  listarRegistrosPorSesion(sesionId: number): Observable<RegistroAsistenciaApiDto[]> {
    const params = new HttpParams({ fromObject: { sesion_id: String(sesionId) } });
    return this.http
      .get<RegistroAsistenciaApiDto[]>(buildApiUrl('registros/'), { params })
      .pipe(catchError((err) => this.fail(err, 'No se pudieron cargar registros.')));
  }

  generarQrToken(materiaId: number, alumnoId: number): Observable<QrGenerateResponse> {
    const params = new HttpParams({
      fromObject: {
        materia_id: String(materiaId),
        alumno_id: String(alumnoId),
      },
    });
    return this.http
      .get<QrGenerateResponse>(buildApiUrl('qr/generate/'), { params })
      .pipe(catchError((err) => this.fail(err, 'No se pudo generar el QR.')));
  }

  segundosRestantesSesion(sesion: SesionAsistenciaApiDto): number {
    const fin = new Date(sesion.fecha_fin_teorica).getTime();
    return Math.max(0, Math.floor((fin - Date.now()) / 1000));
  }

  private fail(error: unknown, fallback: string): Observable<never> {
    return throwError(() => new Error(this.errorMessage(error, fallback)));
  }

  private errorMessage(error: unknown, fallback: string): string {
    if (error instanceof HttpErrorResponse) {
      const body = error.error;
      if (typeof body === 'string' && body.trim().startsWith('<')) {
        return 'El gateway devolvió HTML en lugar de JSON. Recrea Nginx (docker compose up -d --force-recreate nginx) y confirma que ms-asistencias está activo.';
      }
      if (body && typeof body === 'object') {
        if ('error' in body && body.error) {
          const errField = body.error;
          if (Array.isArray(errField)) {
            return errField.map((item) => String(item)).join(' ');
          }
          const text = String(errField);
          if (text.startsWith('[') && text.endsWith(']')) {
            return text.slice(1, -1).replace(/'/g, '').trim();
          }
          return text;
        }
        if ('message' in body && body.message) {
          return String(body.message);
        }
      }
      if (error.status === 0) {
        return 'Sin conexión con MS-5. Verifica Nginx y ms-asistencias (puerto 8005).';
      }
      if (error.status === 401) {
        return 'Sesión expirada. Vuelve a iniciar sesión.';
      }
    }
    return fallback;
  }
}
