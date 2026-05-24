import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { OnDestroy } from '@angular/core';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { AsistenciasDocenteService, RegistroAsistencia } from '../../../services/docente-services/asistencias-docente.service';

@Component({
  selector: 'app-asistencias-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './asistencias-screen.html',
  styleUrl: './asistencias-screen.scss'
})
export class AsistenciasScreen implements OnDestroy {
  registros: RegistroAsistencia[] = [];
  listaConfirmada = false;
  scanner: Html5QrcodeScanner | null = null;
  resultadoQr = '';
  sesionActiva = false;
  sesionFinalizada = false;
  codigoSesion = '';
  tiempoRestanteSegundos = 0;
  mensajeSesion = 'La sesión aún no inicia.';
  private timerId: ReturnType<typeof setInterval> | null = null;

  constructor(private readonly asistenciasService: AsistenciasDocenteService) {
    this.codigoSesion = this.asistenciasService.generarCodigoSesion();
    this.tiempoRestanteSegundos = this.asistenciasService.duracionSesionSegundos;
  }

  get tiempoTranscurridoSegundos(): number {
    return this.asistenciasService.duracionSesionSegundos - this.tiempoRestanteSegundos;
  }

  get tiempoRestanteFormateado(): string {
    return this.asistenciasService.formatearTiempo(this.tiempoRestanteSegundos);
  }

  get tiempoTranscurridoFormateado(): string {
    return this.asistenciasService.formatearTiempo(this.tiempoTranscurridoSegundos);
  }

  get progresoSesion(): number {
    return Math.min(100, Math.round((this.tiempoTranscurridoSegundos / this.asistenciasService.duracionSesionSegundos) * 100));
  }

  get totalPresentes(): number {
    return this.registros.filter((registro) => registro.estado === 'PRESENTE').length;
  }

  get totalRetardos(): number {
    return this.registros.filter((registro) => registro.estado === 'RETARDO').length;
  }

  get totalRegistros(): number {
    return this.registros.length;
  }

  iniciarSesion(): void {
    this.registros = [];
    this.resultadoQr = '';
    this.codigoSesion = this.asistenciasService.generarCodigoSesion();
    this.tiempoRestanteSegundos = this.asistenciasService.duracionSesionSegundos;
    this.sesionActiva = true;
    this.sesionFinalizada = false;
    this.mensajeSesion = 'Sesión iniciada. La cámara está lista para escanear QR dinámicos.';
    this.iniciarTemporizador();
    setTimeout(() => this.iniciarScanner(), 100);
  }

  finalizarSesion(mensaje = 'La sesión se cerró automáticamente al llegar a cero.'): void {
    if (this.sesionFinalizada) {
      return;
    }

    this.sesionActiva = false;
    this.sesionFinalizada = true;
    this.mensajeSesion = mensaje;
    this.detenerTemporizador();
    this.detenerScanner();
  }

  iniciarTemporizador(): void {
    this.detenerTemporizador();

    this.timerId = setInterval(() => {
      if (!this.sesionActiva) {
        this.detenerTemporizador();
        return;
      }

      if (this.tiempoRestanteSegundos <= 1) {
        this.tiempoRestanteSegundos = 0;
        this.finalizarSesion('La sesión llegó a cero y se cerró automáticamente.');
        return;
      }

      this.tiempoRestanteSegundos -= 1;
    }, 1000);
  }

  detenerTemporizador(): void {
    if (this.timerId) {
      clearInterval(this.timerId);
      this.timerId = null;
    }
  }

  iniciarScanner(): void {
    if (!this.sesionActiva) {
      this.mensajeSesion = 'Primero inicia la sesión de 10 minutos.';
      return;
    }

    if (this.scanner) return;

    this.scanner = new Html5QrcodeScanner(
      'reader',
      {
        fps: 10,
        qrbox: { width: 260, height: 260 },
        rememberLastUsedCamera: true
      },
      false
    );

    this.scanner.render(
      (decodedText) => {
        this.procesarQr(decodedText);
      },
      () => {}
    );
  }

  procesarQr(decodedText: string): void {
    if (!this.sesionActiva) {
      return;
    }

    if (this.tiempoRestanteSegundos <= 0) {
      this.finalizarSesion();
      return;
    }

    const codigoQr = decodedText.trim();

    if (!codigoQr) {
      return;
    }

    const procesado = this.asistenciasService.procesarCodigoQr(codigoQr, this.tiempoTranscurridoSegundos);

    if (!procesado) {
      return;
    }

    this.resultadoQr = codigoQr;

    const existente = this.registros.find((registro) => registro.codigoQr === codigoQr);

    if (existente) {
      existente.hora = procesado.hora;
      existente.estado = procesado.estado;
      existente.tipo = procesado.tipo;
      existente.minuto = procesado.minuto;
      this.mensajeSesion = `${procesado.nombre} ya fue registrado en esta sesión.`;
      return;
    }

    this.registros = [
      this.asistenciasService.crearRegistro(codigoQr, procesado),
      ...this.registros
    ];

    this.mensajeSesion = `${procesado.nombre} registrado como ${procesado.estado === 'PRESENTE' ? 'Presente' : 'Retardo'}.`;
  }

  detenerScanner(): void {
    if (this.scanner) {
      this.scanner.clear().catch(() => {});
      this.scanner = null;
    }
  }

  ngOnDestroy(): void {
    this.detenerTemporizador();
    this.detenerScanner();
  }

  async confirmarLista(): Promise<void> {
    if (this.listaConfirmada) {
      this.mensajeSesion = 'La lista ya fue confirmada.';
      return;
    }

    if (this.registros.length === 0) {
      this.mensajeSesion = 'No hay registros en esta sesión para confirmar.';
      return;
    }

    const confirmar = window.confirm('¿Deseas confirmar esta lista de asistencia? Una vez confirmada no podrá modificarse aquí.');

    if (!confirmar) return;

    this.listaConfirmada = true;
    this.sesionActiva = false;
    this.sesionFinalizada = true;
    this.detenerTemporizador();
    this.detenerScanner();
    this.mensajeSesion = 'Confirmando la lista...';

    try {
      await this.asistenciasService.confirmarSesion(this.codigoSesion, this.registros);
      this.mensajeSesion = 'Lista confirmada por el docente.';
    } catch (e) {
      this.mensajeSesion = 'Error al confirmar la lista. Intenta nuevamente.';
      this.listaConfirmada = false;
    }
  }

  solicitarReinicio(): void {
    const confirmar = window.confirm('¿Deseas solicitar la lista de nuevo (iniciar una nueva sesión)? Se borrarán los registros temporales actuales.');

    if (!confirmar) return;

    // Reiniciar sesión: limpiar registros y volver a iniciar.
    this.registros = [];
    this.listaConfirmada = false;
    this.iniciarSesion();
    this.mensajeSesion = 'Sesión reiniciada. Escanea nuevamente los QR.';
  }

}