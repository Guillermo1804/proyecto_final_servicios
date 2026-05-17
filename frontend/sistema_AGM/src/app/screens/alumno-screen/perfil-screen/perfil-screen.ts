import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';

@Component({
  selector: 'app-perfil-screen',
  standalone: true,
  imports: [
    CommonModule,
    TopbarAdmin,
    BottomNavbarAlumno
  ],
  templateUrl: './perfil-screen.html',
  styleUrl: './perfil-screen.scss'
})
export class PerfilScreen {}