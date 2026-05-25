import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';
import { DropConfirmModal } from '../../../modals/drop-confirm-modal/drop-confirm-modal';
import { HistorialPeriodo, MateriaAlumno, NotasService, ParcialMateria } from '../../../services/alumno-services/notas.service';

@Component({
  selector: 'app-notas-screen',
  standalone: true,
  imports: [
    CommonModule,
    TopbarAdmin,
    BottomNavbarAlumno,
    DropConfirmModal
  ],
  templateUrl: './notas-screen.html',
  styleUrls: ['./notas-screen.scss']
})
export class NotasScreen {

  promedioGeneral = 0;
  progresoPeriodo = 65; // porcentaje de avance del periodo

  materias: MateriaAlumno[] = [];
  historial: HistorialPeriodo[] = [];

  constructor(private readonly notasScreenService: NotasService) {}

  ngOnInit(): void {
    this.materias = this.notasScreenService.recalcularPromedios(
      this.notasScreenService.getMaterias()
    );
    this.historial = this.notasScreenService.getHistorial();
    this.calcularPromedioGeneral();
  }

  // Baja de materia (UI)
  modalVisible = false;
  dropConfirmationText = '';
  dropError: string | null = null;
  dropSuccess: string | null = null;
  materiaSeleccionada: MateriaAlumno | null = null;

  abrirModalBaja(m: MateriaAlumno) {
    if (m.dropped) return;
    this.materiaSeleccionada = m;
    this.dropConfirmationText = '';
    this.dropError = null;
    this.dropSuccess = null;
    this.modalVisible = true;
  }

  cerrarModal() {
    this.modalVisible = false;
    this.materiaSeleccionada = null;
  }

  async confirmarBaja() {
    const m = this.materiaSeleccionada;
    if (!m) return;

    if (this.dropConfirmationText !== 'DARSE DE BAJA') {
      this.dropError = 'Debes escribir "DARSE DE BAJA" para confirmar.';
      return;
    }

    if (m.dropped) {
      this.dropError = 'Ya se realizó la baja de esta materia.';
      return;
    }

    // Llamada al API (placeholder). Usamos el NRC como id temporal.
    try {
      const enrollmentId = encodeURIComponent(m.nrc || m.nrc);
      const res = await fetch(`/api/enrollments/${enrollmentId}/drop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirmation: 'DARSE DE BAJA' })
      });

      if (res.status === 200 || res.status === 201) {
        const data = await res.json().catch(() => ({}));
        this.notasScreenService.marcarBaja(m, data.droppedAt || new Date().toISOString());
        this.dropSuccess = 'Baja realizada correctamente. Se notificó al docente.';
        this.calcularPromedioGeneral();
        setTimeout(() => this.cerrarModal(), 1200);
      } else if (res.status === 409) {
        this.dropError = 'La baja ya fue realizada previamente.';
      } else if (res.status === 400) {
        const err = await res.json().catch(() => null);
        this.dropError = (err && err.message) || 'Solicitud inválida.';
      } else {
        this.dropError = 'Error en el servidor. Intenta más tarde.';
      }
    } catch (err) {
      this.dropError = 'No se pudo conectar con el servidor.';
    }
  }

  toggleExpand(m: MateriaAlumno) {
    m.expandido = !m.expandido;
  }

  private parseValor(valor: any): number | null {
    if (valor === null || valor === undefined) return null;
    if (typeof valor === 'number') return isFinite(valor) ? valor : null;
    const n = Number(valor);
    return Number.isFinite(n) ? n : null;
  }

  actualizarPromedioMateria(m: MateriaAlumno) {
    this.notasScreenService.recalcularPromedioMateria(m);
  }

  calcularPromedioGeneral() {
    this.promedioGeneral = this.notasScreenService.calcularPromedioGeneral(this.materias);
  }

  // Si se editan notas manualmente en UI, llamar a esta función
  onNotaCambio(m: MateriaAlumno, parcial: ParcialMateria, nuevoValor: any) {
    parcial.valor = this.parseValor(nuevoValor);
    this.actualizarPromedioMateria(m);
    this.calcularPromedioGeneral();
  }

}