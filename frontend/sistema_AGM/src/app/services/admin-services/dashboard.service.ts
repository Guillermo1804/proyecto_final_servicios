import { Injectable } from '@angular/core';

export interface DashboardStat {
  icono: string;
  titulo: string;
  valor: string;
  estado: string;
  tipo: 'verde' | 'gris' | 'rojo';
  color: 'azul' | 'naranja' | 'gris';
}

export interface DashboardActivity {
  icono: string;
  accion: string;
  usuario: string;
  fecha: string;
  color: 'azul' | 'rojo' | 'negro';
}

export interface DashboardAction {
  label: string;
  route: string;
}

export interface DashboardActions {
  periodos: DashboardAction;
  docentes: DashboardAction;
  actividad: DashboardAction;
}

@Injectable({
  providedIn: 'root'
})
export class DashboardService {

  private readonly estadisticas: DashboardStat[] = [
    {
      icono: 'bi-people',
      titulo: 'TOTAL DE ALUMNOS',
      valor: '1,284',
      estado: '+4%',
      tipo: 'verde',
      color: 'azul'
    },
    {
      icono: 'bi-mortarboard',
      titulo: 'TOTAL DE DOCENTES',
      valor: '86',
      estado: 'Estable',
      tipo: 'gris',
      color: 'azul'
    },
    {
      icono: 'bi-journal-bookmark',
      titulo: 'MATERIAS ACTIVAS',
      valor: '42',
      estado: 'Activo',
      tipo: 'verde',
      color: 'naranja'
    },
    {
      icono: 'bi-calendar',
      titulo: 'PERIODOS ACTIVOS',
      valor: '2',
      estado: 'Finaliza hoy',
      tipo: 'rojo',
      color: 'gris'
    }
  ];

  private readonly actividades: DashboardActivity[] = [
    {
      icono: 'bi-person-plus',
      accion: 'Registro de Estudiante',
      usuario: 'Carlos Ortega',
      fecha: 'Hace 10 min',
      color: 'azul'
    },
    {
      icono: 'bi-list-check',
      accion: 'Modificación de Notas',
      usuario: 'Dra. María Lopez',
      fecha: 'Hace 1 h',
      color: 'negro'
    },
    {
      icono: 'bi-exclamation-triangle',
      accion: 'Error de Conexión API',
      usuario: 'Sistema Central',
      fecha: 'Hace 2 h',
      color: 'rojo'
    },
    {
      icono: 'bi-box-arrow-in-right',
      accion: 'Cierre de Periodo 2023-2',
      usuario: 'Dr. Smith',
      fecha: 'Ayer',
      color: 'negro'
    }
  ];

  private readonly acciones: DashboardActions = {
    periodos: {
      label: 'Configurar ahora',
      route: '/admin/periodos'
    },
    docentes: {
      label: 'Nueva alta docente',
      route: '/admin/docentes'
    },
    actividad: {
      label: 'Ver todo',
      route: '/admin/materias'
    }
  };

  getEstadisticas(): DashboardStat[] {
    return [...this.estadisticas];
  }

  getActividades(): DashboardActivity[] {
    return [...this.actividades];
  }

  getAcciones(): DashboardActions {
    return this.acciones;
  }
}