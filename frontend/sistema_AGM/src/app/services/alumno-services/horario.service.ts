import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';

import { InscripcionMateriaApiDto } from '../../models/alumnos-api.model';
import { AlumnosService } from './alumnos.service';

export interface HorarioDia {
  dia: string;
  numero: number;
  activo: boolean;
}

export interface HorarioMateria {
  hora: string;
  materia: string;
  docente: string;
  aula: string;
  horario: string;
  color: string;
  icono: string;
  dia: string;
}

export interface HorarioResumen {
  horasLectivasTotales: number;
  proyectos: number;
  profesores: number;
}

const DIAS_SEMANA = ['LUN', 'MAR', 'MIÉ', 'JUE', 'VIE'] as const;

const MAPA_DIAS: Record<string, string[]> = {
  LUN: ['LUN', 'L', 'LU', 'LUNES'],
  MAR: ['MAR', 'MA', 'M', 'MARTES'],
  'MIÉ': ['MIÉ', 'MIE', 'MI', 'X', 'MIERCOLES', 'MIÉRCOLES'],
  JUE: ['JUE', 'J', 'JU', 'JUEVES'],
  VIE: ['VIE', 'V', 'VI', 'VIERNES'],
};

@Injectable({ providedIn: 'root' })
export class HorarioService {
  private horarios: HorarioMateria[] = [];
  private loaded = false;

  constructor(private alumnos: AlumnosService) {}

  loadHorarios(): Observable<HorarioMateria[]> {
    return this.alumnos.getMeMaterias(1, 100).pipe(
      map((page) => {
        this.horarios = page.results.flatMap((item) => this.mapInscripcion(item));
        this.loaded = true;
        return this.horarios;
      }),
    );
  }

  getDiaActivo(diaSeleccionado?: string): HorarioDia[] {
    const hoy = new Date().getDate();
    return DIAS_SEMANA.map((dia, index) => ({
      dia,
      numero: hoy + index,
      activo: dia === (diaSeleccionado ?? 'LUN'),
    }));
  }

  getHorarios(): HorarioMateria[] {
    return this.horarios;
  }

  getResumen(): HorarioResumen {
    const materias = new Set(this.horarios.map((h) => h.materia));
    const docentes = new Set(this.horarios.map((h) => h.docente).filter(Boolean));
    return {
      horasLectivasTotales: this.horarios.length,
      proyectos: materias.size,
      profesores: docentes.size,
    };
  }

  getHorariosDelDia(diaSeleccionado: string): HorarioMateria[] {
    return this.horarios.filter((item) => item.dia === diaSeleccionado);
  }

  isLoaded(): boolean {
    return this.loaded;
  }

  private mapInscripcion(item: InscripcionMateriaApiDto): HorarioMateria[] {
    const detail = item.materia_detail as Record<string, unknown> | undefined;
    const horarioTexto = String(item.horario ?? detail?.['horario'] ?? '').trim();
    const materia = String(item.nombre_materia ?? detail?.['nombre'] ?? 'Materia');
    const docente = String(item.docente_nombre ?? detail?.['docente_nombre'] ?? '');
    const aula = String(detail?.['salon'] ?? detail?.['aula'] ?? '—');
    const dias = this.parseDias(horarioTexto);

    if (!dias.length) {
      return [
        {
          hora: this.extractHora(horarioTexto),
          materia,
          docente,
          aula,
          horario: horarioTexto || 'Sin horario',
          color: 'azul',
          icono: 'bi-clock',
          dia: 'LUN',
        },
      ];
    }

    return dias.map((dia, index) => ({
      hora: this.extractHora(horarioTexto),
      materia,
      docente,
      aula,
      horario: horarioTexto,
      color: index % 2 === 0 ? 'azul' : 'naranja',
      icono: 'bi-clock',
      dia,
    }));
  }

  private parseDias(horario: string): string[] {
    if (!horario) {
      return [];
    }
    const tokens = horario
      .toUpperCase()
      .replace(/[\/\s,]+/g, ' ')
      .split(' ')
      .map((t) => t.trim())
      .filter(Boolean);

    const encontrados: string[] = [];
    for (const dia of DIAS_SEMANA) {
      const aliases = MAPA_DIAS[dia] ?? [];
      if (tokens.some((token) => aliases.includes(token))) {
        encontrados.push(dia);
      }
    }
    return encontrados;
  }

  private extractHora(horario: string): string {
    const match = horario.match(/\d{1,2}:\d{2}/);
    return match ? match[0] : '—';
  }
}
