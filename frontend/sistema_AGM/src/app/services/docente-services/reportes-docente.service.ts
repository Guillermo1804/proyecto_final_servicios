import { Injectable } from '@angular/core';

export interface ReporteExportacionItem {
  documento: string;
  materia: string;
  fecha: string;
}

export interface ReporteAcademicoMateriaItem {
  nombre: string;
  grupo: string;
  alumnos: number;
  promedio: number;
  aprobacion: number;
}

export interface ReporteAcademicoPeriodoItem {
  periodo: string;
  activo: boolean;
  resumen: string;
  materias: ReporteAcademicoMateriaItem[];
}

export interface ReporteComparativaItem {
  nombre: string;
  repeticiones: number;
  promedioActual: number;
  promedioAnterior: number;
  variacionPromedio: string;
  aprobacionActual: number;
  aprobacionAnterior: number;
  variacionAprobacion: string;
  periodos: string[];
}

export interface ReportePeriodoEscolarItem {
  nombre: string;
  activo: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ReportesDocenteService {

  private readonly periodosEscolares: ReportePeriodoEscolarItem[] = [
    { nombre: 'Primavera 2024', activo: true },
    { nombre: 'Verano 2024', activo: false },
    { nombre: 'Otoño 2023', activo: false }
  ];

  private readonly historial: ReporteExportacionItem[] = [
    {
      documento: 'Acta Final - IA_1_A',
      materia: 'Inteligencia Artificial I',
      fecha: '12 May 2024, 09:45'
    },
    {
      documento: 'Listado de Asistencia',
      materia: 'Sistemas Operativos',
      fecha: '10 May 2024, 14:20'
    },
    {
      documento: 'Reporte Parcial',
      materia: 'Estructuras de Datos',
      fecha: '08 May 2024, 11:30'
    }
  ];

  private readonly historialAcademico: ReporteAcademicoPeriodoItem[] = [
    {
      periodo: 'Primavera 2024',
      activo: true,
      resumen: 'Periodo actual con 4 materias impartidas y desempeño estable.',
      materias: [
        { nombre: 'Inteligencia Artificial I', grupo: 'IA_1_A', alumnos: 42, promedio: 8.1, aprobacion: 94 },
        { nombre: 'Estructuras de Datos', grupo: 'ED_2_B', alumnos: 38, promedio: 7.4, aprobacion: 86 },
        { nombre: 'Sistemas Operativos', grupo: 'SO_3_A', alumnos: 40, promedio: 8.6, aprobacion: 97 },
        { nombre: 'Redes de Computadoras', grupo: 'RED_1_A', alumnos: 35, promedio: 8.0, aprobacion: 92 }
      ]
    },
    {
      periodo: 'Verano 2024',
      activo: false,
      resumen: 'Periodo concluido. Se conserva como referencia comparativa.',
      materias: [
        { nombre: 'Inteligencia Artificial I', grupo: 'IA_1_A', alumnos: 40, promedio: 7.8, aprobacion: 89 },
        { nombre: 'Estructuras de Datos', grupo: 'ED_2_B', alumnos: 36, promedio: 7.9, aprobacion: 91 },
        { nombre: 'Bases de Datos', grupo: 'BD_2_A', alumnos: 41, promedio: 8.3, aprobacion: 95 }
      ]
    },
    {
      periodo: 'Otoño 2023',
      activo: false,
      resumen: 'Sin actividad registrada en la mayoría de las materias seleccionadas.',
      materias: [
        { nombre: 'Inteligencia Artificial I', grupo: 'IA_1_A', alumnos: 0, promedio: 0, aprobacion: 0 },
        { nombre: 'Estructuras de Datos', grupo: 'ED_2_B', alumnos: 0, promedio: 0, aprobacion: 0 }
      ]
    }
  ];

  private readonly materiasComparadas: ReporteComparativaItem[] = [
    {
      nombre: 'Inteligencia Artificial I',
      repeticiones: 3,
      promedioActual: 8.1,
      promedioAnterior: 7.8,
      variacionPromedio: '+0.3',
      aprobacionActual: 94,
      aprobacionAnterior: 89,
      variacionAprobacion: '+5',
      periodos: ['Otoño 2023', 'Verano 2024', 'Primavera 2024']
    },
    {
      nombre: 'Estructuras de Datos',
      repeticiones: 3,
      promedioActual: 7.4,
      promedioAnterior: 7.9,
      variacionPromedio: '-0.5',
      aprobacionActual: 86,
      aprobacionAnterior: 91,
      variacionAprobacion: '-5',
      periodos: ['Otoño 2023', 'Verano 2024', 'Primavera 2024']
    }
  ];

  getHistorial(): ReporteExportacionItem[] {
    return this.historial.map((item) => ({ ...item }));
  }

  getPeriodosEscolares(): ReportePeriodoEscolarItem[] {
    return this.periodosEscolares.map((periodo) => ({ ...periodo }));
  }

  getHistorialAcademico(): ReporteAcademicoPeriodoItem[] {
    return this.historialAcademico.map((periodo) => ({
      ...periodo,
      materias: periodo.materias.map((materia) => ({ ...materia }))
    }));
  }

  getMateriasComparadas(): ReporteComparativaItem[] {
    return this.materiasComparadas.map((item) => ({
      ...item,
      periodos: [...item.periodos]
    }));
  }
}