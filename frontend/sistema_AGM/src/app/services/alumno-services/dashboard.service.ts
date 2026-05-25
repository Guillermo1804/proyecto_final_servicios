import { Injectable } from '@angular/core';

export interface AlumnoResumen {
  nombre: string;
  matricula: string;
  tipoFormacion?: string;
  periodoActivo?: string;
}

export interface MateriaActual {
  nrc: string;
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

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private readonly alumnoBase: AlumnoResumen = {
    nombre: 'Roberto García',
    matricula: 'A01234567',
    tipoFormacion: 'Presencial',
    periodoActivo: '2026-1'
  };

  private readonly materiasActualesBase: MateriaActual[] = [
    { nrc: '12345', nombre: 'Cálculo Estructural', docente: 'Mtro. Juan Pérez', seccion: 'A' },
    { nrc: '23456', nombre: 'Resistencia de Materiales', docente: 'Dra. Laura Méndez', seccion: 'B' },
    { nrc: '34567', nombre: 'Ética Profesional', docente: 'Mtra. Ana López', seccion: 'C' }
  ];

  private readonly materiasHoyBase: MateriaHoy[] = [
    {
      icono: 'bi-compass',
      color: 'azul',
      materia: 'Cálculo Estructural',
      aula: 'Aula B-204, Edificio Norte',
      horario: '08:00-10:00'
    },
    {
      icono: 'bi-tree',
      color: 'naranja',
      materia: 'Resistencia de Materiales',
      aula: 'Laboratorio de Ingeniería',
      horario: '10:30-12:30'
    },
    {
      icono: 'bi-vector-pen',
      color: 'morado',
      materia: 'Ética Profesional',
      aula: 'Aula Magna 1',
      horario: '14:00-16:00'
    }
  ];

  private readonly evaluacionesBase: EvaluacionItem[] = [
    { materia: 'Arquitectura de Software', fecha: '30 de Mayo', valor: '25%' },
    { materia: 'Sistemas Operativos', fecha: '05 de Junio', valor: '30%' },
    { materia: 'Base de Datos II', fecha: '12 de Junio', valor: '20%' }
  ];

  getAlumno(): AlumnoResumen {
    return { ...this.alumnoBase };
  }

  getMateriasActuales(): MateriaActual[] {
    return this.materiasActualesBase.map((m) => ({ ...m }));
  }

  getMateriasHoy(): MateriaHoy[] {
    return this.materiasHoyBase.map((m) => ({ ...m }));
  }

  getEvaluaciones(): EvaluacionItem[] {
    return this.evaluacionesBase.map((e) => ({ ...e }));
  }
}
