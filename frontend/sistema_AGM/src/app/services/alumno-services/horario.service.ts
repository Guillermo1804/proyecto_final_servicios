import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';

import { InscripcionMateriaApiDto } from '../../models/alumnos-api.model';
import { AlumnosService } from './alumnos.service';
import { DIAS_SEMANA_LAB, extractHoraParaDia, parseDiasDesdeHorario } from './horario-dias.util';

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

const DIAS_SEMANA = DIAS_SEMANA_LAB;
const COLORES_MATERIA = ['azul', 'naranja', 'morado', 'gris'] as const;

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
    const aula = String(detail?.['salon'] ?? detail?.['aula'] ?? '').trim();
    const dias = this.parseDias(horarioTexto);
    const color = this.colorParaMateria(item);

    if (!dias.length) {
      return [
        {
          hora: extractHoraParaDia(horarioTexto, 'LUN'),
          materia,
          docente,
          aula,
          horario: horarioTexto || 'Sin horario',
          color,
          icono: 'bi-clock',
          dia: 'LUN',
        },
      ];
    }

    return dias.map((dia) => ({
      hora: extractHoraParaDia(horarioTexto, dia),
      materia,
      docente,
      aula,
      horario: horarioTexto,
      color,
      icono: 'bi-clock',
      dia,
    }));
  }

  private colorParaMateria(item: InscripcionMateriaApiDto): string {
    const id = Number(item.materia_id ?? 0);
    const key = id > 0 ? id : String(item.nrc ?? item.nombre_materia ?? '').length;
    return COLORES_MATERIA[Math.abs(key) % COLORES_MATERIA.length];
  }

  private parseDias(horario: string): string[] {
    return parseDiasDesdeHorario(horario);
  }
}
