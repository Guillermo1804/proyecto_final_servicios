import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';

@Component({
  selector: 'app-notas-screen',
  standalone: true,
  imports: [
    CommonModule,
    TopbarAdmin,
    BottomNavbarAlumno
  ],
  templateUrl: './notas-screen.html',
  styleUrl: './notas-screen.scss'
})
export class NotasScreen {

  materias = [
    {
      icono: 'bi-calculator',
      color: 'azul',
      nombre: 'Cálculo Multivariado',
      nrc: '14502',
      profesor: 'Ricardo Méndez',
      promedio: 9.2,
      promedioColor: 'verde',
      expandido: true,
      parciales: [
        { titulo: 'Parcial 1', valor: '9.5' },
        { titulo: 'Parcial 2', valor: '8.9' },
        { titulo: 'Final', valor: '--', activo: true }
      ]
    },
    {
      icono: 'bi-beaker',
      color: 'naranja',
      nombre: 'Física Cuántica I',
      nrc: '18221',
      profesor: 'Elena Soto',
      promedio: 5.8,
      promedioColor: 'rojo',
      expandido: false
    },
    {
      icono: 'bi-code-slash',
      color: 'morado',
      nombre: 'Estructura de Datos',
      nrc: '12003',
      profesor: 'Iván Torres',
      promedio: 8.4,
      promedioColor: 'verde',
      expandido: false
    },
    {
      icono: 'bi-book',
      color: 'gris',
      nombre: 'Ética Profesional',
      nrc: '11109',
      profesor: 'Carlos Ruiz',
      promedio: 10.0,
      promedioColor: 'verde',
      expandido: false
    }
  ];

  historial = [
    {
      periodo: 'Otoño 2023',
      materias: 6,
      aprobadas: 6
    },
    {
      periodo: 'Primavera 2023',
      materias: 7,
      aprobadas: 6
    }
  ];

}