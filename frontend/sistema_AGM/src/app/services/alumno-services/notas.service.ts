import { Injectable } from '@angular/core';

export interface ParcialMateria {
  titulo: string;
  valor: number | null;
  porcentaje: number;
  activo?: boolean;
}

export interface MateriaAlumno {
  icono: string;
  color: string;
  nombre: string;
  nrc: string;
  profesor: string;
  promedio: number;
  promedioColor: string;
  expandido: boolean;
  parciales: ParcialMateria[];
  dropped?: boolean;
  droppedAt?: string;
  access?: boolean;
}

export interface HistorialPeriodo {
  periodo: string;
  materias: number;
  aprobadas: number;
}

@Injectable({
  providedIn: 'root'
})
export class NotasService {

  private readonly materiasBase: MateriaAlumno[] = [
    {
      icono: 'bi-calculator',
      color: 'azul',
      nombre: 'Cálculo Multivariado',
      nrc: '14502',
      profesor: 'Ricardo Méndez',
      promedio: 9.2,
      promedioColor: 'verde',
      expandido: true,
      parciales: [
        { titulo: 'Parcial 1', valor: 9.5, porcentaje: 30 },
        { titulo: 'Parcial 2', valor: 8.9, porcentaje: 30 },
        { titulo: 'Final', valor: null, porcentaje: 40, activo: true }
      ]
    },
    {
      icono: 'bi-beaker',
      color: 'naranja',
      nombre: 'Física Cuántica I',
      nrc: '18221',
      profesor: 'Elena Soto',
      promedio: 5.8,
      promedioColor: 'rojo',
      expandido: false,
      parciales: [
        { titulo: 'Parcial 1', valor: 5.5, porcentaje: 40 },
        { titulo: 'Parcial 2', valor: 6.2, porcentaje: 60 }
      ]
    },
    {
      icono: 'bi-code-slash',
      color: 'morado',
      nombre: 'Estructura de Datos',
      nrc: '12003',
      profesor: 'Iván Torres',
      promedio: 8.4,
      promedioColor: 'verde',
      expandido: false,
      parciales: [
        { titulo: 'Parcial 1', valor: 8.6, porcentaje: 50 },
        { titulo: 'Parcial 2', valor: 8.2, porcentaje: 50 }
      ]
    },
    {
      icono: 'bi-book',
      color: 'gris',
      nombre: 'Ética Profesional',
      nrc: '11109',
      profesor: 'Carlos Ruiz',
      promedio: 10.0,
      promedioColor: 'verde',
      expandido: false,
      parciales: [
        { titulo: 'Parcial 1', valor: 10.0, porcentaje: 100 }
      ]
    }
  ];

  private readonly historial: HistorialPeriodo[] = [
    { periodo: 'Otoño 2023', materias: 6, aprobadas: 6 },
    { periodo: 'Primavera 2023', materias: 7, aprobadas: 6 }
  ];

  getMaterias(): MateriaAlumno[] {
    return this.materiasBase.map((materia) => ({
      ...materia,
      parciales: materia.parciales.map((parcial) => ({ ...parcial }))
    }));
  }

  getHistorial(): HistorialPeriodo[] {
    return this.historial.map((item) => ({ ...item }));
  }

  calcularPromedioMateria(materia: MateriaAlumno): number {
    const parciales = Array.isArray(materia.parciales) ? materia.parciales : [];
    let sumaPeso = 0;
    let suma = 0;

    for (const parcial of parciales) {
      const nota = this.parseValor(parcial.valor);
      const peso = Number(parcial.porcentaje) || 0;

      if (nota !== null && peso > 0) {
        suma += nota * (peso / 100);
        sumaPeso += peso;
      }
    }

    return sumaPeso > 0 ? Number((suma / (sumaPeso / 100)).toFixed(2)) : 0;
  }

  recalcularPromedioMateria(materia: MateriaAlumno): MateriaAlumno {
    materia.promedio = this.calcularPromedioMateria(materia);
    materia.promedioColor = this.obtenerColorPromedio(materia.promedio);
    return materia;
  }

  recalcularPromedios(materias: MateriaAlumno[]): MateriaAlumno[] {
    return materias.map((materia) => this.recalcularPromedioMateria(materia));
  }

  calcularPromedioGeneral(materias: MateriaAlumno[]): number {
    const promedios = materias.map((materia) => Number(materia.promedio) || 0);

    if (!promedios.length) {
      return 0;
    }

    const suma = promedios.reduce((acumulado, valor) => acumulado + valor, 0);
    return Number((suma / promedios.length).toFixed(2));
  }

  obtenerColorPromedio(promedio: number): string {
    if (promedio >= 8) {
      return 'verde';
    }

    if (promedio >= 6) {
      return 'amarillo';
    }

    return 'rojo';
  }

  getMateriaPorNrc(nrc: string): MateriaAlumno | undefined {
    return this.getMaterias().find((materia) => materia.nrc === nrc);
  }

  marcarBaja(materia: MateriaAlumno, droppedAt: string): MateriaAlumno {
    materia.dropped = true;
    materia.droppedAt = droppedAt;
    materia.access = false;
    return materia;
  }

  private parseValor(valor: number | null | undefined): number | null {
    if (valor === null || valor === undefined) {
      return null;
    }

    return Number.isFinite(valor) ? valor : null;
  }
}
