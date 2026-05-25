import { CommonModule } from '@angular/common';
import { Component, inject, OnDestroy, OnInit } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';
import { QrAsistenciaService, QrAsistenciaSnapshot } from '../../../services/alumno-services/qr-asistencia.service';
import { PerfilService } from '../../../services/alumno-services/perfil.service';

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
export class PerfilScreen implements OnInit, OnDestroy {

  nombre = '';
  matricula: string | null = null;
  readonly qrRefreshSeconds = 5;
  private readonly qrAsistenciaService = inject(QrAsistenciaService);
  private readonly perfilService = inject(PerfilService);

  qrActivo = false;
  qrSnapshot: QrAsistenciaSnapshot | null = null;
  qrCountdown = this.qrRefreshSeconds;
  qrLoading = false;
  qrError: string | null = null;

  private refreshTimerId: number | null = null;
  private countdownTimerId: number | null = null;

  ngOnInit(): void {
    this.qrActivo = false;
    this.perfilService.getProfile().subscribe({
      next: (p) => {
        this.nombre = p.nombre || '';
        this.matricula = p.matricula || null;
      },
      error: () => {
        // keep defaults; component can fallback to token-less state
      }
    });
  }

  ngOnDestroy(): void {
    this.detenerTemporizadores();
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

    this.qrLoading = true;
    this.qrError = null;

    try {
      if (!this.matricula) {
        throw new Error('Matrícula no disponible');
      }

      this.qrSnapshot = await this.qrAsistenciaService.generarQrPersonal(this.matricula);
      this.qrCountdown = this.qrRefreshSeconds;
    } catch (err: any) {
      console.error('Error generando QR:', err);
      this.qrError = 'No se pudo generar el QR de asistencia.' + (err?.message ? ' ' + err.message : '');
    } finally {
      this.qrLoading = false;
    }
  }

  activarQr(): void {
    if (this.qrActivo) {
      return;
    }

    // Si no tenemos matrícula, intentar obtener el perfil antes de activar
    if (!this.matricula) {
      this.qrError = 'Matrícula no disponible. Intentando obtener perfil...';
      this.perfilService.getProfile(true).subscribe({
        next: (p) => {
          this.nombre = p.nombre || '';
          this.matricula = p.matricula || null;
          this.qrError = null;
          if (this.matricula) {
            this.startQr();
          } else {
            this.qrError = 'Matrícula ausente en el perfil.';
          }
        },
        error: () => {
          this.qrError = 'No se pudo obtener el perfil. Comprueba la conexión.';
        }
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
}