import { Injectable } from '@angular/core';
import { Observable, catchError, forkJoin, map, of } from 'rxjs';

import { InscripcionMateriaApiDto } from '../../models/alumnos-api.model';
import { AlumnosService } from './alumnos.service';
import { PeriodosService } from '../admin-services/periodos.service';

export interface AlumnoResumen {
  nombre: string;
  matricula: string;
  tipoFormacion?: string;
  periodoActivo?: string;
}

export interface MateriaActual {
  nrc: string;
  materiaId: number;
  nombre: string;
  docente: string;
  seccion: string;
}

export interface MateriaHoy {
  icono: string;
  color: string;
  materia: string;
  aula: string;
  horario: string;
}

export interface EvaluacionItem {
  materia: string;
  fecha: string;
  valor: string;
}

export interface AlumnoDashboardData {
  materiasActuales: MateriaActual[];
  materiasHoy: MateriaHoy[];
  evaluaciones: EvaluacionItem[];
  periodoActivo: string;
}

const DIA_CODIGOS: Record<number, string> = {
  0: 'DOM',
  1: 'LUN',
  2: 'MAR',
  3: 'MIÉ',
  4: 'JUE',
  5: 'VIE',
  6: 'SÁB',
};

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly iconos = ['bi-journal-bookmark', 'bi-cpu', 'bi-bezier2', 'bi-diagram-3'];
  private readonly colores = ['azul', 'naranja', 'morado', 'gris'];

  constructor(
    private alumnos: AlumnosService,
    private periodos: PeriodosService,
  ) {}

  loadDashboard(): Observable<AlumnoDashboardData> {
    return forkJoin({
      periodo: this.periodos.getPeriodoActivo().pipe(catchError(() => of(null))),
      inscripciones: this.alumnos.getMeMaterias(1, 100),
    }).pipe(map(({ periodo, inscripciones }) => this.mapInscripciones(
      inscripciones.results,
      periodo?.nombre ?? '—',
    )));
  }

  getFechaHoyLabel(): string {
    return new Intl.DateTimeFormat('es-MX', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    }).format(new Date());
  }

  private mapInscripciones(
    inscripciones: InscripcionMateriaApiDto[],
    periodoNombre: string,
  ): AlumnoDashboardData {
    const activas = inscripciones.filter((item) => item.activa !== false);
    const diaHoy = DIA_CODIGOS[new Date().getDay()];

    const materiasActuales: MateriaActual[] = activas.map((item) => {
      const detail = item.materia_detail as Record<string, unknown> | undefined;
      return {
        nrc: String(item.nrc ?? detail?.['nrc'] ?? '—'),
        materiaId: Number(item.materia_id ?? 0),
        nombre: String(item.nombre_materia ?? detail?.['nombre'] ?? 'Materia'),
        docente: String(item.docente_nombre ?? detail?.['docente_nombre'] ?? '—'),
        seccion: String(detail?.['seccion'] ?? detail?.['clave'] ?? item.nrc ?? '—'),
      };
    });

    const materiasHoy: MateriaHoy[] = activas
      .filter((item) => this.inscripcionEsHoy(item, diaHoy))
      .map((item, index) => {
        const detail = item.materia_detail as Record<string, unknown> | undefined;
        const horario = String(item.horario ?? detail?.['horario'] ?? 'Sin horario registrado');
        return {
          icono: this.iconos[index % this.iconos.length],
          color: this.colores[index % this.colores.length],
          materia: String(item.nombre_materia ?? detail?.['nombre'] ?? 'Materia'),
          aula: String(detail?.['salon'] ?? detail?.['aula'] ?? '—'),
          horario,
        };
      });

    return {
      materiasActuales,
      materiasHoy,
      evaluaciones: [],
      periodoActivo: periodoNombre,
    };
  }

  private inscripcionEsHoy(item: InscripcionMateriaApiDto, diaHoy: string): boolean {
    const horario = String(item.horario ?? '').toUpperCase();
    if (!horario.trim()) {
      return diaHoy === 'LUN';
    }
    const tokens = horario
      .replace(/[\/\s,]+/g, ' ')
      .split(' ')
      .map((t) => t.trim())
      .filter(Boolean);

    const mapa: Record<string, string[]> = {
      LUN: ['LUN', 'L', 'LU', 'LUNES'],
      MAR: ['MAR', 'MA', 'M', 'MARTES'],
      'MIÉ': ['MIÉ', 'MIE', 'MI', 'X', 'MIERCOLES', 'MIÉRCOLES'],
      JUE: ['JUE', 'J', 'JU', 'JUEVES'],
      VIE: ['VIE', 'V', 'VI', 'VIERNES'],
      SÁB: ['SÁB', 'SAB', 'SA', 'SABADO', 'SÁBADO'],
      DOM: ['DOM', 'D', 'DO', 'DOMINGO'],
    };

    const validos = mapa[diaHoy] ?? [];
    return tokens.some((token) => validos.includes(token));
  }
}
