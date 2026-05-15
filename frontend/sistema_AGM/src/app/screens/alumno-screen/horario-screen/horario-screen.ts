import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';

@Component({
  selector: 'app-horario-screen',
  standalone: true,
  imports: [
    CommonModule,
    TopbarAdmin,
    BottomNavbarAlumno
  ],
  templateUrl: './horario-screen.html',
  styleUrl: './horario-screen.scss'
})
export class HorarioScreen {

  dias = [
    { dia: 'LUN', numero: 15, activo: true },
    { dia: 'MAR', numero: 16, activo: false },
    { dia: 'MIÉ', numero: 17, activo: false },
    { dia: 'JUE', numero: 18, activo: false },
    { dia: 'VIE', numero: 19, activo: false }
  ];

  horarios = [
    {
      hora: '08:00',
      materia: 'Cálculo Diferencial',
      docente: 'Dr. Alberto Rodríguez',
      aula: 'Aula 402',
      horario: '08:00 - 09:30',
      color: 'azul',
      icono: 'bi-clock'
    },
    {
      hora: '10:00',
      materia: 'Física Cuántica I',
      docente: 'Dra. Elena Martínez',
      aula: 'Lab Gamma',
      horario: '10:00 - 11:30',
      color: 'naranja',
      icono: 'bi-clock'
    },
    {
      hora: '12:00',
      materia: 'Receso / Almuerzo',
      docente: '',
      aula: 'Cafetería Central',
      horario: '12:00 - 13:00',
      color: 'gris',
      icono: 'bi-cup-hot'
    },
    {
      hora: '13:00',
      materia: 'Sistemas Operativos',
      docente: 'Mtro. Javier Solís',
      aula: 'Aula de Cómputo B',
      horario: '13:00 - 14:30',
      color: 'azul',
      icono: 'bi-clock'
    },
    {
      hora: '15:00',
      materia: 'Ingeniería de Software',
      docente: 'Dra. Martha Gomez',
      aula: 'Aula 201',
      horario: '15:00 - 16:30',
      color: 'rojo',
      icono: 'bi-clock'
    }
  ];

}