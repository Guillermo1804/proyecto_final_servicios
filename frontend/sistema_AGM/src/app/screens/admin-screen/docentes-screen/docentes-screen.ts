import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAdmin } from '../../../partials/bottom-navbar-admin/bottom-navbar-admin';

@Component({
  selector: 'app-docentes-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarAdmin],
  templateUrl: './docentes-screen.html',
  styleUrl: './docentes-screen.scss'
})
export class DocentesScreen {

  docentes = [
    {
      nombre: 'Dr. Alejandro Vargas',
      id: '44920-B',
      facultad: 'Ciencias Exactas',
      estado: 'Activo',
      tipo: 'activo',
      foto: '/assets/docente1.jpg'
    },
    {
      nombre: 'Dra. Beatriz Mendoza',
      id: '31255-C',
      facultad: 'Ingeniería',
      estado: 'Licencia',
      tipo: 'licencia',
      foto: '/assets/docente2.jpg'
    },
    {
      nombre: 'Mgter. Carlos Ruiz',
      id: '55621-A',
      facultad: 'Artes y Humanidades',
      estado: 'Activo',
      tipo: 'activo',
      foto: '/assets/docente3.jpg'
    },
    {
      nombre: 'Dra. Diana Soto',
      id: '22091-E',
      facultad: 'Ciencias de la Salud',
      estado: 'Inactivo',
      tipo: 'inactivo',
      foto: '/assets/docente4.jpg'
    }
  ];

}