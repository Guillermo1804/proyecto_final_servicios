import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';

@Component({
  selector: 'app-reportes-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './reportes-screen.html',
  styleUrl: './reportes-screen.scss'
})
export class ReportesScreen {

  historial = [
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

}