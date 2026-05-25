import { Injectable } from '@angular/core';

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

@Injectable({
  providedIn: 'root'
})
export class HorarioService {

  private readonly diasBase: HorarioDia[] = [
    { dia: 'LUN', numero: 15, activo: true },
    { dia: 'MAR', numero: 16, activo: false },
    { dia: 'MIÉ', numero: 17, activo: false },
    { dia: 'JUE', numero: 18, activo: false },
    { dia: 'VIE', numero: 19, activo: false }
  ];

  private readonly horariosBase: HorarioMateria[] = [
    {
      hora: '08:00',
      materia: 'Cálculo Diferencial',
      docente: 'Dr. Alberto Rodríguez',
      aula: 'Aula 402',
      horario: '08:00 - 09:30',
      color: 'azul',
      icono: 'bi-clock',
      dia: 'LUN'
    },
    {
      hora: '10:00',
      materia: 'Física Cuántica I',
      docente: 'Dra. Elena Martínez',
      aula: 'Lab Gamma',
      horario: '10:00 - 11:30',
      color: 'naranja',
      icono: 'bi-clock',
      dia: 'LUN'
    },
    {
      hora: '12:00',
      materia: 'Receso / Almuerzo',
      docente: '',
      aula: 'Cafetería Central',
      horario: '12:00 - 13:00',
      color: 'gris',
      icono: 'bi-cup-hot',
      dia: 'LUN'
    },
    {
      hora: '13:00',
      materia: 'Sistemas Operativos',
      docente: 'Mtro. Javier Solís',
      aula: 'Aula de Cómputo B',
      horario: '13:00 - 14:30',
      color: 'azul',
      icono: 'bi-clock',
      dia: 'MAR'
    },
    {
      hora: '15:00',
      materia: 'Ingeniería de Software',
      docente: 'Dra. Martha Gomez',
      aula: 'Aula 201',
      horario: '15:00 - 16:30',
      color: 'rojo',
      icono: 'bi-clock',
      dia: 'MIÉ'
    },
    {
      hora: '08:00',
      materia: 'Metodología de la Investigación',
      docente: 'Dra. Laura Pérez',
      aula: 'Aula 103',
      horario: '08:00 - 09:30',
      color: 'azul',
      icono: 'bi-clock',
      dia: 'JUE'
    },
    {
      hora: '11:00',
      materia: 'Base de Datos',
      docente: 'Ing. Carlos Ruiz',
      aula: 'Lab SQL',
      horario: '11:00 - 12:30',
      color: 'naranja',
      icono: 'bi-clock',
      dia: 'VIE'
    }
  ];

  private readonly resumen: HorarioResumen = {
    horasLectivasTotales: 18,
    proyectos: 4,
    profesores: 6
  };

  getDias(): HorarioDia[] {
    return this.diasBase.map((dia) => ({ ...dia }));
  }

  getHorarios(): HorarioMateria[] {
    return this.horariosBase.map((horario) => ({ ...horario }));
  }

  getResumen(): HorarioResumen {
    return { ...this.resumen };
  }

  getDiaActivo(diaSeleccionado: string): HorarioDia[] {
    return this.getDias().map((dia) => ({
      ...dia,
      activo: dia.dia === diaSeleccionado
    }));
  }

  getHorariosDelDia(diaSeleccionado: string): HorarioMateria[] {
    return this.getHorarios().filter((horario) => horario.dia === diaSeleccionado);
  }

  getHorasLectivasPorDia(diaSeleccionado: string): number {
    return this.getHorariosDelDia(diaSeleccionado).reduce((total, horario) => {
      const [inicio, fin] = horario.horario.split(' - ');
      const minutosInicio = this.parseHora(inicio);
      const minutosFin = this.parseHora(fin);

      if (minutosInicio === null || minutosFin === null || minutosFin <= minutosInicio) {
        return total;
      }

      return total + ((minutosFin - minutosInicio) / 60);
    }, 0);
  }

  private parseHora(valorHora: string): number | null {
    const partes = valorHora.trim().split(':');

    if (partes.length !== 2) {
      return null;
    }

    const horas = Number(partes[0]);
    const minutos = Number(partes[1]);

    if (!Number.isFinite(horas) || !Number.isFinite(minutos)) {
      return null;
    }

    return horas * 60 + minutos;
  }
}
