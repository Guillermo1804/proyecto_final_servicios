import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAdmin } from '../../../partials/bottom-navbar-admin/bottom-navbar-admin';

@Component({
  selector: 'app-materias-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarAdmin],
  templateUrl: './materias-screen.html',
  styleUrl: './materias-screen.scss'
})
export class MateriasScreen {

  materias = [
    {
      codigo: 'INF-101',
      nombre: 'Introducción a la Programación',
      prerequisito: 'Ninguno',
      facultad: 'INGENIERÍA',
      tipo: 'ingenieria'
    },
    {
      codigo: 'MAT-205',
      nombre: 'Cálculo Diferencial',
      prerequisito: 'Álgebra Superior',
      facultad: 'CIENCIAS',
      tipo: 'ciencias'
    },
    {
      codigo: 'FIS-102',
      nombre: 'Física General II',
      prerequisito: 'Física General I',
      facultad: 'CIENCIAS',
      tipo: 'ciencias'
    },
    {
      codigo: 'HIS-301',
      nombre: 'Historia Universal Moderna',
      prerequisito: 'Historia Universal Antigua',
      facultad: 'ARTES',
      tipo: 'artes'
    }
  ];

}