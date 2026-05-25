import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { finalize } from 'rxjs';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';
import { DropConfirmModal } from '../../../modals/drop-confirm-modal/drop-confirm-modal';
import { AlumnosService } from '../../../services/alumno-services/alumnos.service';
import { HistorialPeriodo, MateriaAlumno, NotasService, ParcialMateria } from '../../../services/alumno-services/notas.service';

@Component({
  selector: 'app-notas-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarAlumno, DropConfirmModal],
  templateUrl: './notas-screen.html',
  styleUrls: ['./notas-screen.scss'],
})
export class NotasScreen implements OnInit {
  promedioGeneral = 0;
  progresoPeriodo = 0;

  materias: MateriaAlumno[] = [];
  historial: HistorialPeriodo[] = [];
  isLoading = true;
  loadError = '';

  modalVisible = false;
  dropConfirmationText = '';
  dropError: string | null = null;
  dropSuccess: string | null = null;
  materiaSeleccionada: MateriaAlumno | null = null;
  bajaEnProgreso = false;

  constructor(
    private readonly notasService: NotasService,
    private readonly alumnosService: AlumnosService,
  ) {}

  ngOnInit(): void {
    this.cargarNotas();
  }

  private cargarNotas(): void {
    this.isLoading = true;
    this.loadError = '';

    this.notasService
      .loadMaterias()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (materias) => {
          this.materias = materias;
          this.historial = this.notasService.getHistorial();
          this.calcularPromedioGeneral();
        },
        error: () => {
          this.loadError = 'No se pudieron cargar tus calificaciones.';
          this.materias = [];
        },
      });
  }

  abrirModalBaja(m: MateriaAlumno): void {
    if (m.dropped) {
      return;
    }
    this.materiaSeleccionada = m;
    this.dropConfirmationText = '';
    this.dropError = null;
    this.dropSuccess = null;
    this.modalVisible = true;
  }

  cerrarModal(): void {
    this.modalVisible = false;
    this.materiaSeleccionada = null;
  }

  confirmarBaja(): void {
    const m = this.materiaSeleccionada;
    if (!m) {
      return;
    }

    if (this.dropConfirmationText !== 'DARSE DE BAJA') {
      this.dropError = 'Debes escribir "DARSE DE BAJA" para confirmar.';
      return;
    }

    if (m.dropped) {
      this.dropError = 'Ya se realizo la baja de esta materia.';
      return;
    }

    if (!m.alumnoId || !m.materiaId) {
      this.dropError = 'No se encontro la inscripcion para dar de baja.';
      return;
    }

    this.bajaEnProgreso = true;
    this.dropError = null;

    this.alumnosService.bajaMateria(m.alumnoId, m.materiaId).subscribe({
      next: () => {
        this.notasService.marcarBaja(m);
        this.dropSuccess = 'Baja realizada correctamente.';
        this.calcularPromedioGeneral();
        this.bajaEnProgreso = false;
        setTimeout(() => this.cerrarModal(), 1200);
      },
      error: (err) => {
        this.dropError = AlumnosService.extractError(err, 'No se pudo completar la baja.');
        this.bajaEnProgreso = false;
      },
    });
  }

  toggleExpand(m: MateriaAlumno): void {
    m.expandido = !m.expandido;
  }

  calcularPromedioGeneral(): void {
    this.promedioGeneral = this.notasService.calcularPromedioGeneral(this.materias);
  }
}
