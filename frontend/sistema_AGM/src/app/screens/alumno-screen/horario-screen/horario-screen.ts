import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';
import { HorarioDia, HorarioMateria, HorarioResumen, HorarioService } from '../../../services/alumno-services/horario.service';

@Component({
  selector: 'app-horario-screen',
  standalone: true,
  imports: [
    CommonModule,
    TopbarAdmin,
    BottomNavbarAlumno
  ],
  templateUrl: './horario-screen.html',
  styleUrl: './horario-screen.scss'
})
export class HorarioScreen {

  dias: HorarioDia[] = [];

  diaSeleccionado = 'LUN';
  horarios: HorarioMateria[] = [];
  resumen: HorarioResumen = {
    horasLectivasTotales: 0,
    proyectos: 0,
    profesores: 0
  };

  isLoading = true;
  loadError = '';

  constructor(private readonly horarioScreenService: HorarioService) {}

  ngOnInit(): void {
    this.dias = this.horarioScreenService.getDiaActivo(this.diaSeleccionado);
    this.horarioScreenService.loadHorarios().subscribe({
      next: () => {
        this.horarios = this.horarioScreenService.getHorarios();
        this.resumen = this.horarioScreenService.getResumen();
        this.isLoading = false;
      },
      error: () => {
        this.loadError = 'No se pudo cargar tu horario (MS-3). Inicia sesion como alumno.';
        this.isLoading = false;
      },
    });
  }

  seleccionarDia(dia: string) {
    this.diaSeleccionado = dia;
    this.dias = this.horarioScreenService.getDiaActivo(dia);
  }

  get horariosDelDia(): HorarioMateria[] {
    return this.horarioScreenService.getHorariosDelDia(this.diaSeleccionado);
  }

}