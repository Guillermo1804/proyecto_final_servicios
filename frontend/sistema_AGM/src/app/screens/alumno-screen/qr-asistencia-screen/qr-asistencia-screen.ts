import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';
import { FacadeService } from '../../../services/facade.service';
import { Subscription, interval, switchMap, startWith } from 'rxjs';

@Component({
  selector: 'app-qr-asistencia-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, TopbarAdmin, BottomNavbarAlumno],
  templateUrl: './qr-asistencia-screen.html',
  styleUrl: './qr-asistencia-screen.scss',
})
export class QrAsistenciaScreen implements OnInit, OnDestroy {
  materias: { id: number; label: string }[] = [];
  selectedMateriaId = 0;
  alumnoId = 0;
  encodedPayload = '';
  expiresIn = 30;
  sesionId: number | null = null;
  loading = false;
  errorMessage = '';
  private refreshSub?: Subscription;

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    this.facade.getMisMateriasAlumno().subscribe({
      next: (body) => {
        const rows = this.facade.extractList<{
          materia_id?: number;
          alumno?: { id?: number };
          materia_detail?: { nombre?: string; nrc?: string };
        }>(body);
        if (rows.length && rows[0].alumno?.id) {
          this.alumnoId = rows[0].alumno.id;
        }
        this.materias = rows
          .filter((r) => r.materia_id != null)
          .map((r) => ({
            id: r.materia_id as number,
            label: r.materia_detail?.nombre ?? `Materia ${r.materia_id}`,
          }));
        if (this.materias.length) {
          this.selectedMateriaId = this.materias[0].id;
          this.startQrRefresh();
        }
      },
      error: () => {
        this.errorMessage = 'No se pudieron cargar tus materias.';
      },
    });
  }

  ngOnDestroy(): void {
    this.refreshSub?.unsubscribe();
  }

  onMateriaChange(): void {
    this.startQrRefresh();
  }

  get qrImageUrl(): string {
    if (!this.encodedPayload) {
      return '';
    }
    return `https://api.qrserver.com/v1/create-qr-code/?size=280x280&data=${encodeURIComponent(this.encodedPayload)}`;
  }

  private startQrRefresh(): void {
    this.refreshSub?.unsubscribe();
    if (!this.selectedMateriaId || !this.alumnoId) {
      return;
    }
    this.refreshSub = interval(30_000)
      .pipe(
        startWith(0),
        switchMap(() => {
          this.loading = true;
          this.errorMessage = '';
          return this.facade.generateQr(this.selectedMateriaId, this.alumnoId);
        }),
      )
      .subscribe({
        next: (res) => {
          this.loading = false;
          if (res.error) {
            this.errorMessage = res.error;
            this.encodedPayload = '';
            return;
          }
          this.encodedPayload = res.encoded_payload ?? '';
          this.expiresIn = res.expires_in ?? 30;
          this.sesionId = res.sesion_id ?? null;
          if (!this.encodedPayload) {
            this.errorMessage =
              'No hay sesión de asistencia activa para esta materia. Pide al docente que inicie el pase de lista.';
          }
        },
        error: (err) => {
          this.loading = false;
          this.encodedPayload = '';
          this.errorMessage =
            err?.error?.error ??
            'No se pudo generar el código QR. Verifica que el docente haya iniciado la sesión.';
        },
      });
  }
}
