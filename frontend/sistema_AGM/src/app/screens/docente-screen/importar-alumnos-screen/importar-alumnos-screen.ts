import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';

@Component({
  selector: 'app-importar-alumnos-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './importar-alumnos-screen.html',
  styleUrl: './importar-alumnos-screen.scss'
})
export class ImportarAlumnosScreen {

  codigoMateria = '';

  alumnos = [
    {
      matricula: '202300156',
      nombre: 'Martínez González, Ana Laura',
      correo: 'a.martinez@buap.mx'
    },
    {
      matricula: '202300198',
      nombre: 'Rodríguez Sosa, Carlos Alberto',
      correo: 'c.rodriguez@buap.mx'
    },
    {
      matricula: '202300245',
      nombre: 'Vázquez Ruiz, Diana Sofía',
      correo: 'd.vazquez@buap.mx'
    },
    {
      matricula: '202300312',
      nombre: 'Gutiérrez Pech, Jorge Luis',
      correo: 'j.gutierrez@buap.mx'
    }
  ];

  constructor(private route: ActivatedRoute) {
    this.codigoMateria = this.route.snapshot.paramMap.get('id') ?? '';
  }

}