import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { BottomNavbarAdmin } from "../../../partials/bottom-navbar-admin/bottom-navbar-admin";
import { TopbarAdmin } from "../../../partials/topbar-admin/topbar-admin";

@Component({
  selector: 'app-dashboard-docente-screen',
  standalone: true,
  imports: [CommonModule, BottomNavbarDocente, TopbarAdmin],
  templateUrl: './dashboard-screen.html',
  styleUrl: './dashboard-screen.scss'
})
export class DashboardScreen {

  clasesHoy = [
    {
      hora: '08:00-10:00',
      materia: 'Cálculo Integral',
      grupo: 'Grupo A - Ingeniería Civil',
      aula: 'Aula Magna 302',
      icono: 'bi-broadcast',
      activo: true
    },
    {
      hora: '11:30-13:30',
      materia: 'Física Mecánica',
      grupo: 'Grupo B - Ingeniería Mecánica',
      aula: 'Laboratorio L4',
      icono: 'bi-people',
      activo: false
    }
  ];

  pendientes = [
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

  notificaciones = [
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

}