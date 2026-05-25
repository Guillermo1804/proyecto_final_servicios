import { Injectable } from '@angular/core';
import { Observable, map, of } from 'rxjs';

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

@Injectable({ providedIn: 'root' })
export class HorarioService {
  private readonly diasBase: HorarioDia[] = [
    { dia: 'LUN', numero: 15, activo: true },
    { dia: 'MAR', numero: 16, activo: false },
    { dia: 'MIÉ', numero: 17, activo: false },
    { dia: 'JUE', numero: 18, activo: false },
    { dia: 'VIE', numero: 19, activo: false },
  ];

  private horarios: HorarioMateria[] = [];
  private loaded = false;

  constructor(private alumnos: AlumnosService) {}

  loadHorarios(): Observable<HorarioMateria[]> {
    return this.alumnos.getMeMaterias(1, 50).pipe(
      map((page) => {
        this.horarios = page.results.flatMap((item) => this.mapInscripcion(item));
        this.loaded = true;
        return this.horarios;
      }),
    );
  }

  getDiaActivo(diaSeleccionado?: string): HorarioDia[] {
    return this.diasBase.map((dia) => ({
      ...dia,
      activo: dia.dia === (diaSeleccionado ?? 'LUN'),
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
    const horarioTexto = String(item.horario ?? detail?.['horario'] ?? '');
    const materia = String(item.nombre_materia ?? detail?.['nombre'] ?? 'Materia');
    const docente = String(item.docente_nombre ?? detail?.['docente_nombre'] ?? '');

    if (!horarioTexto) {
      return [
        {
          hora: '—',
          materia,
          docente,
          aula: '—',
          horario: 'Sin horario',
          color: 'azul',
          icono: 'bi-clock',
          dia: 'LUN',
        },
      ];
    }

    return [
      {
        hora: horarioTexto.slice(0, 5),
        materia,
        docente,
        aula: '—',
        horario: horarioTexto,
        color: 'azul',
        icono: 'bi-clock',
        dia: 'LUN',
      },
    ];
  }
}
