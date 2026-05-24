import { Injectable } from '@angular/core';

export interface DashboardClaseItem {
  hora: string;
  materia: string;
  grupo: string;
  aula: string;
  icono: string;
  activo: boolean;
  alumnosInscritos: number;
  asistenciaHoy: number;
}

export interface DashboardPendienteItem {
  icono: string;
  color: 'rojo' | 'azul';
  titulo: string;
  detalle: string;
}

export interface DashboardNotificacionItem {
  fecha: string;
  asunto: string;
  emisor: string;
}

export interface DashboardResumenMateriaItem {
  materia: string;
  grupo: string;
  alumnosInscritos: number;
  asistenciaHoy: number;
  estado: 'Activa' | 'Pendiente' | 'Finalizada';
}

@Injectable({
  providedIn: 'root'
})
export class DashboardDocenteService {

  private readonly clasesHoy: DashboardClaseItem[] = [
    {
      hora: '08:00-10:00',
      materia: 'Cálculo Integral',
      grupo: 'Grupo A - Ingeniería Civil',
      aula: 'Aula Magna 302',
      icono: 'bi-broadcast',
      activo: true,
      alumnosInscritos: 38,
      asistenciaHoy: 92
    },
    {
      hora: '11:30-13:30',
      materia: 'Física Mecánica',
      grupo: 'Grupo B - Ingeniería Mecánica',
      aula: 'Laboratorio L4',
      icono: 'bi-people',
      activo: false,
      alumnosInscritos: 34,
      asistenciaHoy: 84
    },
    {
      hora: '15:00-17:00',
      materia: 'Programación Orientada a Objetos',
      grupo: 'Grupo C - Ingeniería en Sistemas',
      aula: 'Aula 204',
      icono: 'bi-laptop',
      activo: false,
      alumnosInscritos: 41,
      asistenciaHoy: 88
    }
  ];

  private readonly pendientes: DashboardPendienteItem[] = [
    {
      icono: 'bi-clipboard2-alert',
      color: 'rojo',
      titulo: 'Práctica: Leyes de Newton',
      detalle: '12 entregas nuevas'
    },
    {
      icono: 'bi-clipboard-check',
      color: 'azul',
      titulo: 'Proyecto Final Parcial',
      detalle: '4 entregas nuevas'
    }
  ];

  private readonly notificaciones: DashboardNotificacionItem[] = [
    {
      fecha: 'Hoy, 10:15',
      asunto: 'Cierre de actas - Periodo Otoño 2023',
      emisor: 'Dirección Académica'
    },
    {
      fecha: 'Ayer, 16:40',
      asunto: 'Nueva solicitud de examen extraordinario',
      emisor: 'Control Escolar'
    }
  ];

  getClasesHoy(): DashboardClaseItem[] {
    return this.clasesHoy.map((clase) => ({ ...clase }));
  }

  getPendientes(): DashboardPendienteItem[] {
    return this.pendientes.map((pendiente) => ({ ...pendiente }));
  }

  getNotificaciones(): DashboardNotificacionItem[] {
    return this.notificaciones.map((notificacion) => ({ ...notificacion }));
  }

  getTotalMateriasAsignadas(): number {
    return this.clasesHoy.length;
  }

  getTotalAlumnosInscritos(): number {
    return this.clasesHoy.reduce((total, clase) => total + clase.alumnosInscritos, 0);
  }

  getPorcentajeAsistenciaDelDia(): number {
    const totalAlumnos = this.getTotalAlumnosInscritos();

    if (totalAlumnos === 0) {
      return 0;
    }

    const asistenciaPonderada = this.clasesHoy.reduce(
      (total, clase) => total + (clase.alumnosInscritos * clase.asistenciaHoy),
      0
    );

    return Math.round((asistenciaPonderada / totalAlumnos) * 10) / 10;
  }

  getResumenMaterias(): DashboardResumenMateriaItem[] {
    return this.clasesHoy.map((clase) => ({
      materia: clase.materia,
      grupo: clase.grupo,
      alumnosInscritos: clase.alumnosInscritos,
      asistenciaHoy: clase.asistenciaHoy,
      estado: clase.activo ? 'Activa' : 'Pendiente'
    }));
  }
}