import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAdmin } from '../../../partials/bottom-navbar-admin/bottom-navbar-admin';

@Component({
  selector: 'app-periodos-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarAdmin],
  templateUrl: './periodos-screen.html',
  styleUrl: './periodos-screen.scss'
})
export class PeriodosScreen {

  periodos = [
    {
      nombre: '2024-1',
      estado: 'Activo',
      tipo: 'activo',
      fechaInicio: '15/01/2024',
      icono: 'azul'
    },
    {
      nombre: '2024-2',
      estado: 'Próximo',
      tipo: 'proximo',
      fechaInicio: '15/08/2024',
      icono: 'gris'
    },
    {
      nombre: '2023-2',
      estado: 'Cerrado',
      tipo: 'cerrado',
      fechaInicio: '15/08/2023',
      icono: 'gris'
    },
    {
      nombre: '2023-1',
      estado: 'Cerrado',
      tipo: 'cerrado',
      fechaInicio: '15/01/2023',
      icono: 'gris'
    }
  ];

}