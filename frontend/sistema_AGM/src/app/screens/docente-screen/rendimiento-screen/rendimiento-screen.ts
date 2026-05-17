import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';

@Component({
  selector: 'app-rendimiento-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './rendimiento-screen.html',
  styleUrl: './rendimiento-screen.scss'
})
export class RendimientoScreen {

  codigoMateria = '';

  estudiantesRiesgo = [
    {
      iniciales: 'LM',
      nombre: 'Lucía Méndez',
      matricula: '20210452',
      promedio: '58.5',
      asistencia: '72%'
    },
    {
      iniciales: 'RG',
      nombre: 'Roberto Gómez',
      matricula: '20210981',
      promedio: '62.0',
      asistencia: '85%'
    },
    {
      iniciales: 'SF',
      nombre: 'Sofía Figueroa',
      matricula: '20220110',
      promedio: '64.5',
      asistencia: '60%'
    },
    {
      iniciales: 'DV',
      nombre: 'Daniel Vera',
      matricula: '20210622',
      promedio: '68.0',
      asistencia: '92%'
    }
  ];

  constructor(private route: ActivatedRoute) {
    this.codigoMateria = this.route.snapshot.paramMap.get('id') ?? '';
  }

}