import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { RouterLink } from '@angular/router';
@Component({
  selector: 'app-detalle-materia-screen',
  standalone: true,
  imports: [CommonModule, BottomNavbarDocente, TopbarAdmin,RouterLink],
  templateUrl: './detalle-materia-screen.html',
  styleUrl: './detalle-materia-screen.scss'
})
export class DetalleMateriaScreen {

  codigoMateria = '';

  alumnos = [
    {
      iniciales: 'AG',
      nombre: 'Alonso García, Roberto',
      matricula: '202300124',
      asistencia: '98%'
    },
    {
      iniciales: 'BC',
      nombre: 'Barrera Cruz, Sofía',
      matricula: '202300456',
      asistencia: '85%'
    },
    {
      iniciales: 'DV',
      nombre: 'Díaz Valdés, Marco',
      matricula: '202300891',
      asistencia: '62%'
    },
    {
      iniciales: 'LM',
      nombre: 'López Mora, Elena',
      matricula: '202300321',
      asistencia: '100%'
    }
  ];

  constructor(private route: ActivatedRoute) {
    this.codigoMateria = this.route.snapshot.paramMap.get('id') ?? '';
  }

}