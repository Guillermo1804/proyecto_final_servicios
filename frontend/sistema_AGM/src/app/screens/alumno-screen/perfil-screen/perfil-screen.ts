import { CommonModule } from '@angular/common';
import { Component, inject, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';
import { InscripcionMateriaApiDto } from '../../../models/alumnos-api.model';
import { AlumnosService } from '../../../services/alumno-services/alumnos.service';
import { StatsAlumnoMateriaResponse } from '../../../models/asistencias-api.model';
import { AsistenciasService } from '../../../services/asistencias.service';
import { QrAsistenciaService, QrAsistenciaSnapshot } from '../../../services/alumno-services/qr-asistencia.service';
import { PerfilService } from '../../../services/alumno-services/perfil.service';
import { FotoPerfilService } from '../../../services/alumno-services/foto-perfil.service';

@Component({
  selector: 'app-perfil-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, TopbarAdmin, BottomNavbarAlumno],
  templateUrl: './perfil-screen.html',
  styleUrl: './perfil-screen.scss',
})
export class PerfilScreen implements OnInit, OnDestroy {
  nombre = '';
  matricula: string | null = null;
  alumnoId: number | null = null;
  materiasInscritas: InscripcionMateriaApiDto[] = [];
  materiaQrId: number | null = null;

  readonly qrRefreshSeconds = 5;
  private readonly qrAsistenciaService = inject(QrAsistenciaService);
  private readonly perfilService = inject(PerfilService);
  private readonly alumnosService = inject(AlumnosService);
  private readonly asistenciasService = inject(AsistenciasService);
  private readonly fotoPerfilService = inject(FotoPerfilService);

  fotoUrl: string | null = null;
  fotoIniciales = 'AG';
  fotoSubiendo = false;
  fotoError = '';
  private fotoUserKey = '';

  qrActivo = false;
  asistenciaStats: StatsAlumnoMateriaResponse | null = null;
  asistenciaCargando = false;
  asistenciaError: string | null = null;
  qrSnapshot: QrAsistenciaSnapshot | null = null;
  qrCountdown = this.qrRefreshSeconds;
  qrLoading = false;
  qrError: string | null = null;

  private refreshTimerId: number | null = null;
  private countdownTimerId: number | null = null;

  ngOnInit(): void {
    this.qrActivo = false;
    this.cargarPerfilYmaterias();
  }

  ngOnDestroy(): void {
    this.detenerTemporizadores();
  }

  private cargarPerfilYmaterias(): void {
    this.perfilService.getProfile().subscribe({
      next: (p) => {
        this.nombre = p.nombre || '';
        this.matricula = p.matricula || null;
        this.fotoIniciales = this.fotoPerfilService.iniciales(this.nombre);
        if (!this.fotoUserKey) {
          this.fotoUserKey = this.fotoPerfilService.buildUserKey({ email: p.email });
          this.refrescarFoto();
        }
      },
    });

    this.alumnosService.getMe().subscribe({
      next: (alumno) => {
        this.alumnoId = alumno.id;
        this.fotoUserKey = this.fotoPerfilService.buildUserKey({
          alumnoId: alumno.id,
          usuarioId: alumno.usuario_id,
          email: alumno.email,
        });
        this.refrescarFoto();
        void this.cargarResumenAsistencia();
      },
    });

    this.alumnosService.getMeMaterias(1, 100).subscribe({
      next: (page) => {
        this.materiasInscritas = page.results.filter((item) => item.activa !== false);
        if (!this.materiaQrId && this.materiasInscritas.length === 1) {
          this.materiaQrId = Number(this.materiasInscritas[0].materia_id);
        }
        void this.cargarResumenAsistencia();
      },
    });
  }

  onMateriaQrChange(materiaId: number | null): void {
    this.materiaQrId = materiaId;
    void this.cargarResumenAsistencia();
  }

  async cargarResumenAsistencia(): Promise<void> {
    if (!this.materiaQrId || !this.alumnoId) {
      this.asistenciaStats = null;
      this.asistenciaError = null;
      return;
    }

    this.asistenciaCargando = true;
    this.asistenciaError = null;
    try {
      this.asistenciaStats = await firstValueFrom(
        this.asistenciasService.statsAlumnoMateria(this.alumnoId, this.materiaQrId),
      );
    } catch (err: unknown) {
      this.asistenciaStats = null;
      this.asistenciaError =
        err instanceof Error ? err.message : 'No se pudo cargar tu resumen de asistencia.';
    } finally {
      this.asistenciaCargando = false;
    }
  }

  get materiaQrSeleccionada(): InscripcionMateriaApiDto | null {
    return (
      this.materiasInscritas.find((item) => Number(item.materia_id) === this.materiaQrId) ?? null
    );
  }

  private iniciarTemporizadores(): void {
    this.detenerTemporizadores();
    this.qrCountdown = this.qrRefreshSeconds;

    this.countdownTimerId = window.setInterval(() => {
      if (this.qrCountdown > 0) {
        this.qrCountdown -= 1;
      }
    }, 1000);

    this.refreshTimerId = window.setInterval(() => {
      void this.regenerarQr();
    }, this.qrRefreshSeconds * 1000);
  }

  private detenerTemporizadores(): void {
    if (this.refreshTimerId !== null) {
      window.clearInterval(this.refreshTimerId);
      this.refreshTimerId = null;
    }

    if (this.countdownTimerId !== null) {
      window.clearInterval(this.countdownTimerId);
      this.countdownTimerId = null;
    }
  }

  async regenerarQr(): Promise<void> {
    if (!this.qrActivo) {
      return;
    }

    if (!this.materiaQrId || !this.alumnoId) {
      this.qrError = 'Selecciona una materia y asegúrate de tener perfil de alumno cargado.';
      return;
    }

    this.qrLoading = true;
    this.qrError = null;

    try {
      this.qrSnapshot = await this.qrAsistenciaService.generarQrDesdeBackend(
        this.materiaQrId,
        this.alumnoId,
      );
      this.qrCountdown = this.qrRefreshSeconds;
    } catch (err: unknown) {
      const mensaje = err instanceof Error ? err.message : 'Error desconocido';
      this.qrError = `No se pudo generar el QR. ${mensaje}`;
    } finally {
      this.qrLoading = false;
    }
  }

  activarQr(): void {
    if (this.qrActivo) {
      return;
    }

    if (!this.materiaQrId) {
      this.qrError = 'Selecciona la materia para la que pasarás lista.';
      return;
    }

    if (!this.alumnoId) {
      this.qrError = 'Cargando datos del alumno...';
      void firstValueFrom(this.alumnosService.getMe())
        .then((alumno) => {
          this.alumnoId = alumno.id;
          void this.cargarResumenAsistencia();
          this.startQr();
        })
        .catch(() => {
          this.qrError = 'No se pudo obtener tu perfil de alumno (MS-3).';
        });
      return;
    }

    this.startQr();
  }

  private startQr(): void {
    this.qrActivo = true;
    void this.regenerarQr();
    this.iniciarTemporizadores();
  }

  private refrescarFoto(): void {
    this.fotoUrl = this.fotoPerfilService.getFotoDataUrl(this.fotoUserKey);
  }

  abrirSelectorFoto(): void {
    const input = document.getElementById('foto-perfil-input') as HTMLInputElement | null;
    input?.click();
  }

  onFotoSeleccionada(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file || !this.fotoUserKey) {
      return;
    }

    this.fotoSubiendo = true;
    this.fotoError = '';
    this.fotoPerfilService.guardarDesdeArchivo(this.fotoUserKey, file).subscribe({
      next: (dataUrl) => {
        this.fotoUrl = dataUrl;
        this.fotoSubiendo = false;
      },
      error: (err) => {
        this.fotoSubiendo = false;
        this.fotoError = err instanceof Error ? err.message : 'No se pudo guardar la foto.';
      },
    });
  }

  quitarFoto(): void {
    if (!this.fotoUserKey) {
      return;
    }
    this.fotoPerfilService.eliminarFoto(this.fotoUserKey);
    this.fotoUrl = null;
    this.fotoError = '';
  }
}
