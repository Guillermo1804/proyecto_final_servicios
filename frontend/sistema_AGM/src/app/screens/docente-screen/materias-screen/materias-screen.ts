import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { RouterLink } from '@angular/router';
import { TopbarAdmin } from "../../../partials/topbar-admin/topbar-admin";

@Component({
  selector: 'app-materias-docente-screen',
  standalone: true,
  imports: [CommonModule, BottomNavbarDocente, RouterLink, TopbarAdmin],
  templateUrl: './materias-screen.html',
  styleUrl: './materias-screen.scss'
})
export class MateriasScreen {

  materias = [
    {
      codigo: 'INF-402',
      nombre: 'Estructuras de Datos II',
      facultad: 'Facultad de Ingeniería',
      alumnos: 32,
      progreso: 65,
      horario: 'Lunes - Miércoles (08:00 - 10:00)'
    },
    {
      codigo: 'INF-310',
      nombre: 'Sistemas Operativos',
      facultad: 'Facultad de Ingeniería',
      alumnos: 28,
      progreso: 42,
      horario: 'Martes - Jueves (10:00 - 12:00)'
    },
    {
      codigo: 'INF-501',
      nombre: 'Inteligencia Artificial',
      facultad: 'Facultad de Ingeniería',
      alumnos: 24,
      progreso: 88,
      horario: 'Viernes (14:00 - 18:00)'
    }
  ];

}