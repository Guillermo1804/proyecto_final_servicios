import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';

@Component({
  selector: 'app-calificaciones-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './calificaciones-screen.html',
  styleUrl: './calificaciones-screen.scss'
})
export class CalificacionesScreen {

  estudiantes = [
    {
      foto: '/assets/alumno1.jpg',
      nombre: 'García, María Fernanda',
      id: '20210459',
      parcial1: '9.5',
      parcial2: '8.0',
      final: '8.5',
      riesgo: false
    },
    {
      foto: '/assets/alumno2.jpg',
      nombre: 'Ruiz, Carlos Alberto',
      id: '20210872',
      parcial1: '4.0',
      parcial2: '5.5',
      final: '--',
      riesgo: true
    },
    {
      foto: '/assets/alumno3.jpg',
      nombre: 'Méndez, Lucía Isabel',
      id: '20220115',
      parcial1: '7.0',
      parcial2: '7.5',
      final: '8.0',
      riesgo: false
    },
    {
      foto: '/assets/alumno4.jpg',
      nombre: 'López, Jorge Eduardo',
      id: '20210223',
      parcial1: '10.0',
      parcial2: '9.0',
      final: '9.5',
      riesgo: false
    }
  ];

}