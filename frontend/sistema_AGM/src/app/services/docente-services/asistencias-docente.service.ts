import { Injectable } from '@angular/core';
import { Observable, firstValueFrom, map } from 'rxjs';

import {
  RegistroAsistenciaApiDto,
  RegistrarAsistenciaResponse,
  SesionAsistenciaApiDto,
} from '../../models/asistencias-api.model';
import { SesionHistorialItemDto } from '../../models/asistencias-api.model';
import { AsistenciasService } from '../asistencias.service';
import { descargarPaseListaPdf } from './pase-lista-pdf.util';
import { AuthService } from '../auth.service';
import { DocentesService } from '../admin-services/docentes.service';
import { AlumnosService } from '../alumno-services/alumnos.service';

export type EstadoAsistencia = 'PRESENTE' | 'RETARDO';

export interface RegistroAsistencia {
  alumnoId: number;
  nombre: string;
  iniciales: string;
  hora: string;
  estado: EstadoAsistencia;
  tipo: 'puntual' | 'tardanza';
  codigoQr: string;
  minuto: number;
}

export interface ContextoMateriaSesion {
  id: number;
  nrc: string;
  clave: string;
  materia: string;
  seccion: string;
  salon: string;
}

@Injectable({
  providedIn: 'root',
})
export class AsistenciasDocenteService {
  readonly duracionSesionSegundos = 10 * 60;

  constructor(
    private readonly asistencias: AsistenciasService,
    private readonly auth: AuthService,
    private readonly docentes: DocentesService,
    private readonly alumnosMs3: AlumnosService,
  ) {}

  generarCodigoSesion(sesionId?: number): string {
    return sesionId ? `SES-${sesionId}` : `SES-${Date.now().toString(36).toUpperCase()}`;
  }

  formatearTiempo(segundos: number): string {
    const minutos = Math.floor(segundos / 60);
    const resto = segundos % 60;
    return `${minutos.toString().padStart(2, '0')}:${resto.toString().padStart(2, '0')}`;
  }

  formatearHora(fecha: Date): string {
    return fecha.toLocaleTimeString('es-MX', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  }

  obtenerIniciales(nombre: string): string {
    return nombre
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((fragmento) => fragmento.charAt(0).toUpperCase())
      .join('');
  }

  resolverDocenteId(): Observable<number> {
    const user = this.auth.getStoredUser();
    if (!user?.id) {
      throw new Error('Usuario no autenticado.');
    }
    return this.docentes.findDocenteApiByUsuarioId(user.id).pipe(
      map((docente) => {
        if (!docente?.id) {
          throw new Error('No hay docente vinculado a tu usuario.');
        }
        return docente.id;
      }),
    );
  }

  cargarNombresAlumnos(materiaId: number): Observable<Map<number, string>> {
    return this.alumnosMs3.getAlumnosPorMateria(materiaId, 1, 500).pipe(
      map((page) => {
        const mapa = new Map<number, string>();
        for (const item of page.results) {
          const alumno = item.alumno;
          if (!alumno?.id) {
            continue;
          }
          mapa.set(alumno.id, AlumnosService.mapAlumnoNombre(alumno));
        }
        return mapa;
      }),
    );
  }

  async iniciarSesionEnBackend(materiaId: number): Promise<SesionAsistenciaApiDto> {
    const docenteId = await firstValueFrom(this.resolverDocenteId());
    const response = await firstValueFrom(this.asistencias.iniciarSesion(materiaId, docenteId));
    return response.sesion;
  }

  async obtenerSesionActiva(materiaId: number): Promise<SesionAsistenciaApiDto | null> {
    const response = await firstValueFrom(this.asistencias.obtenerSesionActiva(materiaId));
    return response.activa && response.sesion ? response.sesion : null;
  }

  async registrarQrEscaneado(
    encodedPayload: string,
    nombres: Map<number, string>,
  ): Promise<RegistroAsistencia> {
    const resultado = await firstValueFrom(this.asistencias.registrarAsistencia(encodedPayload));
    return this.mapRegistroApi(resultado, encodedPayload, nombres);
  }

  async sincronizarRegistros(
    sesionId: number,
    nombres: Map<number, string>,
  ): Promise<RegistroAsistencia[]> {
    const items = await firstValueFrom(this.asistencias.listarRegistrosPorSesion(sesionId));
    return items.map((item) => this.mapRegistroList(item, nombres));
  }

  async confirmarSesion(sesionId: number): Promise<void> {
    await firstValueFrom(this.asistencias.confirmarSesion(sesionId));
  }

  async solicitarNuevaLista(sesionId: number): Promise<void> {
    await firstValueFrom(this.asistencias.solicitarNuevaLista(sesionId));
  }

  async cerrarSesion(sesionId: number): Promise<void> {
    await firstValueFrom(this.asistencias.cerrarSesion(sesionId));
  }

  async sincronizarRegistrosSesion(
    sesionId: number,
    nombres: Map<number, string>,
  ): Promise<RegistroAsistencia[]> {
    return this.sincronizarRegistros(sesionId, nombres);
  }

  async obtenerSesionPendiente(materiaId: number): Promise<SesionAsistenciaApiDto | null> {
    const response = await firstValueFrom(this.asistencias.obtenerSesionPendiente(materiaId));
    return response.sesion;
  }

  async statsSesion(sesionId: number) {
    return firstValueFrom(this.asistencias.statsSesion(sesionId));
  }

  async statsAlumnoMateria(alumnoId: number, materiaId: number) {
    return firstValueFrom(this.asistencias.statsAlumnoMateria(alumnoId, materiaId));
  }

  formatPorcentajeAsistencia(porcentaje: number, totalRegistros: number): string {
    if (totalRegistros <= 0) {
      return 'Sin registros';
    }
    return `${Math.round(porcentaje)}%`;
  }

  async listarHistorialSesiones(
    materiaId: number,
    dias = 30,
    limit = 30,
  ): Promise<SesionHistorialItemDto[]> {
    const response = await firstValueFrom(
      this.asistencias.listarHistorialSesiones(materiaId, dias, limit),
    );
    return response.sesiones ?? [];
  }

  async descargarReporteAsistencias(materiaId: number, formato: 'pdf' | 'xlsx' = 'pdf'): Promise<Blob> {
    return firstValueFrom(this.asistencias.descargarReporteAsistencias(materiaId, formato));
  }

  descargarListaPdf(
    registros: RegistroAsistencia[],
    materia: ContextoMateriaSesion,
    sesionId: number,
    fechaSesion?: string,
  ): void {
    descargarPaseListaPdf(registros, materia, sesionId, fechaSesion);
  }

  descargarListaCsv(
    registros: RegistroAsistencia[],
    materia: ContextoMateriaSesion,
    sesionId: number,
  ): void {
    const filas = [
      ['Nombre', 'Estado', 'Hora', 'Minuto'],
      ...registros.map((r) => [r.nombre, r.estado, r.hora, String(r.minuto)]),
    ];
    const csv = filas
      .map((fila) => fila.map((celda) => `"${String(celda).replace(/"/g, '""')}"`).join(','))
      .join('\n');
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    const fecha = new Date().toISOString().slice(0, 10);
    anchor.href = url;
    anchor.download = `asistencia_${materia.clave}_sesion${sesionId}_${fecha}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  segundosRestantes(sesion: SesionAsistenciaApiDto): number {
    return this.asistencias.segundosRestantesSesion(sesion);
  }

  private mapRegistroApi(
    resultado: RegistrarAsistenciaResponse,
    codigoQr: string,
    nombres: Map<number, string>,
  ): RegistroAsistencia {
    const estadoUi = this.estadoUi(resultado.estado);
    const nombre = nombres.get(resultado.alumno_id) ?? `Alumno ${resultado.alumno_id}`;
    return {
      alumnoId: resultado.alumno_id,
      nombre,
      iniciales: this.obtenerIniciales(nombre),
      hora: this.formatearHora(new Date()),
      estado: estadoUi,
      tipo: estadoUi === 'PRESENTE' ? 'puntual' : 'tardanza',
      codigoQr,
      minuto: resultado.minuto_registro,
    };
  }

  private mapRegistroList(
    item: RegistroAsistenciaApiDto,
    nombres: Map<number, string>,
  ): RegistroAsistencia {
    const estadoUi = this.estadoUi(item.estado);
    const nombre = nombres.get(item.alumno_id) ?? `Alumno ${item.alumno_id}`;
    const fecha = new Date(item.fecha_registro);
    return {
      alumnoId: item.alumno_id,
      nombre,
      iniciales: this.obtenerIniciales(nombre),
      hora: this.formatearHora(fecha),
      estado: estadoUi,
      tipo: estadoUi === 'PRESENTE' ? 'puntual' : 'tardanza',
      codigoQr: '',
      minuto: item.minuto_registro,
    };
  }

  private estadoUi(estado: string): EstadoAsistencia {
    return estado?.toLowerCase() === 'retardo' ? 'RETARDO' : 'PRESENTE';
  }
}
