import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';
import { AuthService } from '../../../services/auth.service';
import { PerfilService } from '../../../services/alumno-services/perfil.service';
import { AlumnoResumen, MateriaActual, MateriaHoy, EvaluacionItem } from '../../../services/alumno-services/dashboard.service';

@Component({
  selector: 'app-dashboard-screen',
  standalone: true,
  imports: [
    CommonModule,
    TopbarAdmin,
    BottomNavbarAlumno
  ],
  templateUrl: './dashboard-screen.html',
  styleUrl: './dashboard-screen.scss'
})
export class DashboardScreen implements OnInit {

  alumno: AlumnoResumen = { nombre: '', matricula: '', tipoFormacion: '—', periodoActivo: '—' };
  rolLabel = '';
  emailUsuario = '';
  materiasActuales: MateriaActual[] = [];
  materiasHoy: MateriaHoy[] = [];
  evaluaciones: EvaluacionItem[] = [];
  perfilLoading = true;

  constructor(
    private auth: AuthService,
    private perfilService: PerfilService,
  ) {}

  ngOnInit(): void {
    this.rolLabel = this.auth.getRoleLabel();
    this.auth.refreshCurrentUser().subscribe({
      next: (user) => {
        this.emailUsuario = user?.email || '';
      },
    });

    this.perfilService.getProfile(true).subscribe({
      next: (perfil) => {
        this.alumno = {
          nombre: perfil.nombre,
          matricula: perfil.matricula,
          tipoFormacion: perfil.carrera || '—',
          periodoActivo: '—',
        };
        this.perfilLoading = false;
      },
      error: () => {
        const user = this.auth.getStoredUser();
        this.alumno = {
          nombre: user?.nombre || 'Usuario',
          matricula: user?.email || '—',
          tipoFormacion: '—',
          periodoActivo: '—',
        };
        this.perfilLoading = false;
      },
    });

    this.materiasActuales = [];
    this.materiasHoy = [];
    this.evaluaciones = [];
  }

}