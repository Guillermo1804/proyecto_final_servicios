import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';

@Component({
  selector: 'app-dashboard-screen',
  standalone: true,
  imports: [
    CommonModule,
    TopbarAdmin,
    BottomNavbarAlumno
  ],
  templateUrl: './dashboard-screen.html',
  styleUrl: './dashboard-screen.scss'
})
export class DashboardScreen {

  materiasHoy = [
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

  evaluaciones = [
    {
      materia: 'Arquitectura de Software',
      fecha: '30 de Mayo',
      valor: '25%'
    },
    {
      materia: 'Sistemas Operativos',
      fecha: '05 de Junio',
      valor: '30%'
    },
    {
      materia: 'Base de Datos II',
      fecha: '12 de Junio',
      valor: '20%'
    }
  ];

}