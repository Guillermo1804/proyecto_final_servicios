import { Injectable } from '@angular/core';

export type EstadoAsistencia = 'PRESENTE' | 'RETARDO';

export interface RegistroAsistencia {
  nombre: string;
  iniciales: string;
  hora: string;
  estado: EstadoAsistencia;
  tipo: 'puntual' | 'tardanza';
  codigoQr: string;
  minuto: number;
}

export interface RegistroProcesado {
  hora: string;
  nombre: string;
  iniciales: string;
  estado: EstadoAsistencia;
  tipo: 'puntual' | 'tardanza';
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
  providedIn: 'root'
})
export class AsistenciasDocenteService {

  readonly duracionSesionSegundos = 10 * 60;
  readonly limitePresenteSegundos = 5 * 60;

  generarCodigoSesion(): string {
    return `QR-${Date.now().toString(36).toUpperCase()}`;
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
      second: '2-digit'
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

  obtenerNombreDesdeQr(codigoQr: string): string {
    try {
      const data = JSON.parse(codigoQr) as { nombre?: string; nombreCompleto?: string; alumno?: string };

      return data.nombreCompleto || data.nombre || data.alumno || codigoQr;
    } catch {
      const partes = codigoQr.split('|').map((parte) => parte.trim()).filter(Boolean);

      if (partes.length > 1) {
        return partes[0];
      }

      return codigoQr.length > 34 ? `${codigoQr.slice(0, 31)}...` : codigoQr;
    }
  }

  procesarCodigoQr(codigoQr: string, segundosTranscurridos: number): RegistroProcesado | null {
    const codigoLimpio = codigoQr.trim();

    if (!codigoLimpio) {
      return null;
    }

    const nombre = this.obtenerNombreDesdeQr(codigoLimpio);
    const iniciales = this.obtenerIniciales(nombre);
    const hora = this.formatearHora(new Date());
    const estado: EstadoAsistencia = segundosTranscurridos <= this.limitePresenteSegundos ? 'PRESENTE' : 'RETARDO';
    const tipo: 'puntual' | 'tardanza' = estado === 'PRESENTE' ? 'puntual' : 'tardanza';
    const minuto = Math.floor(segundosTranscurridos / 60);

    return {
      hora,
      nombre,
      iniciales,
      estado,
      tipo,
      minuto
    };
  }

  crearRegistro(codigoQr: string, procesado: RegistroProcesado): RegistroAsistencia {
    return {
      codigoQr: codigoQr.trim(),
      ...procesado
    };
  }

  // Placeholder para confirmar la sesión en el backend.
  // Actualmente devuelve una promesa resuelta; reemplazar por llamada HttpClient cuando exista API.
  confirmarSesion(
    codigoSesion: string,
    registros: RegistroAsistencia[],
    materia: ContextoMateriaSesion | null
  ): Promise<void> {
    void codigoSesion;
    void registros;
    void materia;

    // Aquí podría enviarse un POST al backend con la lista de asistencias y la materia seleccionada.
    return Promise.resolve();
  }

}