import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { EMPTY, interval, Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { FacadeService } from '../../../services/facade.service';

interface MateriaOption {
  id: number;
  label: string;
}

interface RegistroRow {
  alumnoId: number;
  alumnoNombre: string;
  matricula: string;
  hora: string;
  estado: string;
  tipo: 'puntual' | 'retardo' | 'ausente';
}

@Component({
  selector: 'app-asistencias-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './asistencias-screen.html',
  styleUrl: './asistencias-screen.scss',
})
export class AsistenciasScreen implements OnInit, OnDestroy {
  materias: MateriaOption[] = [];
  selectedMateriaId = 0;
  sesionId: number | null = null;
  sesionActiva = false;
  loading = true;
  iniciando = false;
  errorMessage = '';
  successMessage = '';

  presentes = 0;
  ausentes = 0;
  retardos = 0;

  registros: RegistroRow[] = [];
  modo: 'codigo' | 'scanner' = 'scanner';
  scanner: Html5QrcodeScanner | null = null;
  resultadoQr = '';
  private pollSub?: Subscription;
  private lastScannedPayload = '';

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    const uid = this.facade.getUserId();
    if (!uid) {
      this.loading = false;
      this.errorMessage = 'Sesión inválida.';
      return;
    }
    this.facade.listMateriasDocente(uid, { limit: 100 }).subscribe({
      next: (body) => {
        const rows = this.facade.extractList<{
          id?: number;
          nombre?: string;
          nrc?: string;
        }>(body);
        this.materias = rows
          .filter((m) => m.id)
          .map((m) => ({
            id: m.id as number,
            label: `${m.nrc ?? ''} ${m.nombre ?? ''}`.trim(),
          }));
        if (this.materias.length) {
          this.selectedMateriaId = this.materias[0].id;
          this.refreshSesion();
        } else {
          this.loading = false;
        }
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudieron cargar las materias.';
      },
    });
  }

  onMateriaChange(): void {
    this.detenerScanner();
    this.stopPolling();
    this.sesionId = null;
    this.sesionActiva = false;
    this.registros = [];
    this.refreshSesion();
  }

  refreshSesion(): void {
    if (!this.selectedMateriaId) {
      return;
    }
    this.loading = true;
    this.errorMessage = '';
    this.facade.getSesionActiva(this.selectedMateriaId).subscribe({
      next: (body) => {
        this.loading = false;
        if (body['activa'] && body['sesion']) {
          const sesion = body['sesion'] as { id?: number };
          this.sesionId = sesion.id ?? null;
          this.sesionActiva = true;
          this.loadStatsAndRegistros();
          this.startPolling();
          if (this.modo === 'scanner') {
            setTimeout(() => this.iniciarScanner(), 200);
          }
        } else {
          this.sesionActiva = false;
          this.sesionId = null;
          this.presentes = 0;
          this.retardos = 0;
          this.ausentes = 0;
        }
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudo consultar la sesión activa.';
      },
    });
  }

  iniciarSesion(): void {
    const docenteId = this.facade.getUserId();
    if (!this.selectedMateriaId || !docenteId) {
      this.errorMessage = 'Selecciona materia e inicia sesión como docente.';
      return;
    }
    this.iniciando = true;
    this.errorMessage = '';
    this.facade.iniciarSesionAsistencia(this.selectedMateriaId, docenteId).subscribe({
      next: () => {
        this.iniciando = false;
        this.successMessage = 'Sesión de asistencia iniciada (10 min).';
        this.refreshSesion();
      },
      error: (err) => {
        this.iniciando = false;
        this.errorMessage =
          (err?.error?.error as string) || 'No se pudo iniciar la sesión.';
      },
    });
  }

  cerrarSesion(): void {
    if (!this.sesionId) {
      return;
    }
    this.facade.cerrarSesionAsistencia(this.sesionId).subscribe({
      next: () => {
        this.successMessage = 'Sesión cerrada.';
        this.stopPolling();
        this.detenerScanner();
        this.sesionActiva = false;
        this.sesionId = null;
      },
      error: () => {
        this.errorMessage = 'No se pudo cerrar la sesión.';
      },
    });
  }

  cambiarModo(modo: 'codigo' | 'scanner'): void {
    this.modo = modo;
    if (modo === 'scanner' && this.sesionActiva) {
      setTimeout(() => this.iniciarScanner(), 100);
    } else {
      this.detenerScanner();
    }
  }

  iniciarScanner(): void {
    if (!this.sesionActiva || this.scanner) {
      return;
    }

    this.scanner = new Html5QrcodeScanner('reader', { fps: 10, qrbox: 250 }, false);

    this.scanner.render(
      (decodedText) => {
        if (decodedText === this.lastScannedPayload) {
          return;
        }
        this.lastScannedPayload = decodedText;
        this.resultadoQr = decodedText;
        this.registrarQr(decodedText);
      },
      () => {},
    );
  }

  registrarQr(encodedPayload: string): void {
    this.facade.registrarAsistenciaQr(encodedPayload).subscribe({
      next: (body) => {
        this.successMessage = (body['mensaje'] as string) || 'Asistencia registrada.';
        this.loadStatsAndRegistros();
      },
      error: (err) => {
        this.errorMessage =
          (err?.error?.error as string) || 'QR inválido o ya registrado.';
      },
    });
  }

  loadStatsAndRegistros(): void {
    if (!this.sesionId) {
      return;
    }
    this.facade.getSesionStats(this.sesionId).subscribe({
      next: (stats) => {
        this.presentes = Number(stats['presentes'] ?? 0);
        this.retardos = Number(stats['retardos'] ?? 0);
        this.ausentes = Number(stats['ausentes'] ?? 0);
      },
    });
    this.facade.listRegistrosAsistencia(this.sesionId).subscribe({
      next: (rows) => {
        this.registros = this.mapRegistros(rows);
      },
    });
  }

  private startPolling(): void {
    this.stopPolling();
    this.pollSub = interval(5000)
      .pipe(
        switchMap(() => {
          if (!this.sesionId) {
            return EMPTY;
          }
          return this.facade.getSesionStats(this.sesionId);
        }),
      )
      .subscribe({
        next: (stats) => {
          if (!stats || Array.isArray(stats)) {
            return;
          }
          this.presentes = Number(stats['presentes'] ?? 0);
          this.retardos = Number(stats['retardos'] ?? 0);
          this.ausentes = Number(stats['ausentes'] ?? 0);
          if (this.sesionId) {
            this.facade.listRegistrosAsistencia(this.sesionId).subscribe({
              next: (rows) => {
                this.registros = this.mapRegistros(rows);
              },
            });
          }
        },
      });
  }

  private stopPolling(): void {
    this.pollSub?.unsubscribe();
    this.pollSub = undefined;
  }

  private mapRegistros(rows: unknown[] | null | undefined): RegistroRow[] {
    return (rows ?? []).map((r) => {
      const row = r as {
        alumno_id?: number;
        alumno_nombre?: string;
        matricula?: string;
        estado?: string;
        fecha_registro?: string;
      };
      const estado = (row.estado ?? 'presente').toLowerCase();
      let tipo: RegistroRow['tipo'] = 'puntual';
      if (estado === 'retardo') {
        tipo = 'retardo';
      } else if (estado === 'ausente') {
        tipo = 'ausente';
      }
      const label =
        row.alumno_nombre?.trim() ||
        (row.matricula ? `Mat. ${row.matricula}` : '') ||
        `Alumno #${row.alumno_id ?? '?'}`;
      return {
        alumnoId: row.alumno_id ?? 0,
        alumnoNombre: label,
        matricula: row.matricula ?? '—',
        hora: this.formatHora(row.fecha_registro),
        estado: estado.toUpperCase(),
        tipo,
      };
    });
  }

  private formatHora(iso?: string): string {
    if (!iso) {
      return '--:--:--';
    }
    try {
      return new Date(iso).toLocaleTimeString('es-MX', { hour12: false });
    } catch {
      return iso;
    }
  }

  detenerScanner(): void {
    if (this.scanner) {
      this.scanner.clear().catch(() => {});
      this.scanner = null;
    }
  }

  ngOnDestroy(): void {
    this.stopPolling();
    this.detenerScanner();
  }
}
