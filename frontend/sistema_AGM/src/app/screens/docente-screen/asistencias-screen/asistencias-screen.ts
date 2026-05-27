import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { SesionHistorialItemDto } from '../../../models/asistencias-api.model';
import {
  AsistenciasDocenteService,
  ContextoMateriaSesion,
  RegistroAsistencia,
} from '../../../services/docente-services/asistencias-docente.service';
import {
  MateriaDocenteItem,
  MateriasDocenteService,
} from '../../../services/docente-services/materias-docente.service';

@Component({
  selector: 'app-asistencias-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './asistencias-screen.html',
  styleUrl: './asistencias-screen.scss',
})
export class AsistenciasScreen implements OnInit, OnDestroy {
  registros: RegistroAsistencia[] = [];
  listaConfirmada = false;
  scanner: Html5QrcodeScanner | null = null;
  resultadoQr = '';
  sesionActiva = false;
  sesionFinalizada = false;
  sesionId: number | null = null;
  codigoSesion = '';
  tiempoRestanteSegundos = 0;
  mensajeSesion = 'La sesión aún no inicia.';
  materiasDocente: MateriaDocenteItem[] = [];
  materiaSeleccionadaId: number | null = null;
  procesandoQr = false;
  historialPases: SesionHistorialItemDto[] = [];
  cargandoHistorial = false;
  historialDias = 30;
  exportandoSesionId: number | null = null;
  totalInscritos = 0;
  private nombresAlumnos = new Map<number, string>();
  private timerId: ReturnType<typeof setInterval> | null = null;

  constructor(
    private readonly asistenciasService: AsistenciasDocenteService,
    private readonly materiasService: MateriasDocenteService,
  ) {
    this.tiempoRestanteSegundos = this.asistenciasService.duracionSesionSegundos;
  }

  ngOnInit(): void {
    this.cargarMateriasDocente();
  }

  get materiaSeleccionada(): MateriaDocenteItem | null {
    return this.materiasDocente.find((materia) => materia.id === this.materiaSeleccionadaId) ?? null;
  }

  get etiquetaMateriaSeleccionada(): string {
    const materia = this.materiaSeleccionada;
    if (!materia) {
      return 'Ninguna materia seleccionada';
    }
    return `${materia.clave} · ${materia.materia} · Grupo ${materia.seccion}`;
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
    return Math.min(
      100,
      Math.round(
        (this.tiempoTranscurridoSegundos / this.asistenciasService.duracionSesionSegundos) * 100,
      ),
    );
  }

  get etiquetaChipSesion(): string {
    if (this.sesionActiva) {
      return 'Sesi\u00f3n activa';
    }
    if (this.sesionFinalizada) {
      return 'Sesi\u00f3n cerrada';
    }
    return 'Sesi\u00f3n lista';
  }

  get etiquetaBadgeScanner(): string {
    return this.sesionActiva ? 'Escaneando' : 'Sesi\u00f3n cerrada';
  }

  get mensajeCalloutScanner(): string {
    if (this.materiaSeleccionada) {
      return 'La materia ya est\u00e1 lista. Inicia la sesi\u00f3n para habilitar la c\u00e1mara.';
    }
    return 'Selecciona una materia para habilitar la c\u00e1mara y comenzar a leer QR.';
  }

  readonly mensajeCierreManual = 'La sesi\u00f3n fue cerrada manualmente.';

  get totalPresentes(): number {
    return this.registros.filter((registro) => registro.estado === 'PRESENTE').length;
  }

  get totalRetardos(): number {
    return this.registros.filter((registro) => registro.estado === 'RETARDO').length;
  }

  get totalRegistros(): number {
    return this.registros.length;
  }

  get totalFaltantes(): number {
    if (this.totalInscritos <= 0) {
      return 0;
    }
    return Math.max(0, this.totalInscritos - this.registros.length);
  }

  private aplicarNombresAlumnos(mapa: Map<number, string>): void {
    this.nombresAlumnos = mapa;
    this.totalInscritos = mapa.size;
  }

  async iniciarSesion(): Promise<void> {
    if (!this.materiaSeleccionada) {
      this.mensajeSesion = 'Selecciona una materia antes de activar la cámara.';
      return;
    }

    this.mensajeSesion = 'Iniciando sesi\u00f3n de asistencia...';

    try {
      this.aplicarNombresAlumnos(
        await firstValueFrom(this.asistenciasService.cargarNombresAlumnos(this.materiaSeleccionada.id)),
      );

      const sesion = await this.asistenciasService.iniciarSesionEnBackend(this.materiaSeleccionada.id);
      this.sesionId = sesion.id;
      this.codigoSesion = this.asistenciasService.generarCodigoSesion(sesion.id);
      this.tiempoRestanteSegundos = this.asistenciasService.segundosRestantes(sesion);
      this.registros = [];
      this.resultadoQr = '';
      this.listaConfirmada = false;
      this.sesionActiva = true;
      this.sesionFinalizada = false;
      this.mensajeSesion = `Sesi\u00f3n ${this.codigoSesion} activa. Escanea el QR del alumno.`;
      this.iniciarTemporizador();
      setTimeout(() => this.iniciarScanner(), 100);
    } catch (error) {
      const mensaje = error instanceof Error ? error.message : 'No se pudo iniciar la sesión.';
      this.mensajeSesion = mensaje;
    }
  }

  cargarMateriasDocente(): void {
    this.materiasService.getMaterias().subscribe((materias) => {
      const materiasActivas = materias.filter((materia) => materia.estado === 'Activo');
      this.materiasDocente = materiasActivas.length > 0 ? materiasActivas : materias;
    });
  }

  seleccionarMateria(materiaId: number | null): void {
    this.materiaSeleccionadaId = materiaId;

    if (this.sesionActiva) {
      return;
    }

    if (!this.materiaSeleccionada) {
      this.mensajeSesion = 'Selecciona una materia para continuar.';
      this.historialPases = [];
      return;
    }

    void this.recuperarSesionPendiente(this.materiaSeleccionada.id);
    void this.cargarHistorialPases(this.materiaSeleccionada.id);
  }

  async cargarHistorialPases(materiaId?: number): Promise<void> {
    const id = materiaId ?? this.materiaSeleccionada?.id;
    if (!id) {
      this.historialPases = [];
      return;
    }

    this.cargandoHistorial = true;
    try {
      if (this.nombresAlumnos.size === 0) {
        this.aplicarNombresAlumnos(
          await firstValueFrom(this.asistenciasService.cargarNombresAlumnos(id)),
        );
      }
      this.historialPases = await this.asistenciasService.listarHistorialSesiones(
        id,
        this.historialDias,
      );
    } catch {
      this.historialPases = [];
    } finally {
      this.cargandoHistorial = false;
    }
  }

  formatFechaHistorial(fechaIso: string): string {
    return new Date(fechaIso).toLocaleString('es-MX', {
      dateStyle: 'short',
      timeStyle: 'short',
    });
  }

  etiquetaEstadoSesion(estado: string): string {
    const etiquetas: Record<string, string> = {
      confirmada: 'Confirmada',
      cerrada: 'Pendiente de confirmar',
      activa: 'En curso',
    };
    return etiquetas[estado] ?? estado;
  }

  async descargarPaseHistorial(
    item: SesionHistorialItemDto,
    formato: 'csv' | 'pdf',
  ): Promise<void> {
    const materia = this.materiaSeleccionada;
    if (!materia) {
      return;
    }

    this.exportandoSesionId = item.sesion_id;
    try {
      const registros = await this.asistenciasService.sincronizarRegistrosSesion(
        item.sesion_id,
        this.nombresAlumnos,
      );
      const contexto = this.contextoMateria(materia);
      if (formato === 'csv') {
        this.asistenciasService.descargarListaCsv(registros, contexto, item.sesion_id);
      } else {
        this.asistenciasService.descargarListaPdf(
          registros,
          contexto,
          item.sesion_id,
          item.fecha_inicio,
        );
      }
      this.mensajeSesion = `Pase SES-${item.sesion_id} descargado en ${formato.toUpperCase()}.`;
    } catch (error) {
      this.mensajeSesion =
        error instanceof Error ? error.message : 'No se pudo exportar ese pase de lista.';
    } finally {
      this.exportandoSesionId = null;
    }
  }

  private contextoMateria(materia: MateriaDocenteItem): ContextoMateriaSesion {
    return {
      id: materia.id,
      nrc: materia.nrc,
      clave: materia.clave,
      materia: materia.materia,
      seccion: materia.seccion,
      salon: materia.salon,
    };
  }

  async finalizarSesion(mensaje = 'La sesión se cerró automáticamente al llegar a cero.'): Promise<void> {
    if (this.sesionFinalizada) {
      return;
    }

    this.sesionActiva = false;
    this.sesionFinalizada = true;
    this.detenerTemporizador();
    this.detenerScanner();

    if (!this.sesionId || !this.materiaSeleccionada) {
      this.mensajeSesion = mensaje;
      return;
    }

    try {
      await this.asistenciasService.cerrarSesion(this.sesionId);
      this.registros = await this.asistenciasService.sincronizarRegistrosSesion(
        this.sesionId,
        this.nombresAlumnos,
      );
      this.mensajeSesion =
        `${mensaje} Hay ${this.registros.length} registro(s) en el servidor. ` +
        'Confirma la lista para guardarla definitivamente y descargar el archivo.';
      if (this.materiaSeleccionada) {
        void this.cargarHistorialPases(this.materiaSeleccionada.id);
      }
    } catch {
      this.mensajeSesion =
        `${mensaje} Los escaneos quedan en el servidor; usa «Confirmar lista» o recarga la materia.`;
    }
  }

  private async recuperarSesionPendiente(materiaId: number): Promise<void> {
    if (this.sesionActiva) {
      return;
    }

    try {
      this.aplicarNombresAlumnos(
        await firstValueFrom(this.asistenciasService.cargarNombresAlumnos(materiaId)),
      );

      const activa = await this.asistenciasService.obtenerSesionActiva(materiaId);
      const sesion = activa ?? (await this.asistenciasService.obtenerSesionPendiente(materiaId));
      if (!sesion) {
        this.mensajeSesion = `Materia seleccionada: ${this.etiquetaMateriaSeleccionada}. Ya puedes iniciar la cámara.`;
        return;
      }

      this.sesionId = sesion.id;
      this.codigoSesion = this.asistenciasService.generarCodigoSesion(sesion.id);
      this.listaConfirmada = sesion.estado === 'confirmada';
      this.registros = await this.asistenciasService.sincronizarRegistrosSesion(
        sesion.id,
        this.nombresAlumnos,
      );

      if (sesion.activa && sesion.estado === 'activa') {
        this.sesionActiva = true;
        this.sesionFinalizada = false;
        this.tiempoRestanteSegundos = this.asistenciasService.segundosRestantes(sesion);
        this.mensajeSesion = `Sesión ${this.codigoSesion} reanudada (${this.registros.length} registro(s)).`;
        this.iniciarTemporizador();
        setTimeout(() => this.iniciarScanner(), 100);
        return;
      }

      this.sesionActiva = false;
      this.sesionFinalizada = true;
      this.tiempoRestanteSegundos = 0;
      this.mensajeSesion = this.listaConfirmada
        ? `Lista del día confirmada (${this.registros.length} registro(s)). Puedes descargar el archivo.`
        : `Hay una lista pendiente (${this.registros.length} registro(s)). Confírmala o solicítala de nuevo.`;
    } catch {
      this.mensajeSesion = `Materia seleccionada: ${this.etiquetaMateriaSeleccionada}. Ya puedes iniciar la cámara.`;
    }
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

    if (this.scanner) {
      return;
    }

    this.scanner = new Html5QrcodeScanner(
      'reader',
      {
        fps: 10,
        qrbox: { width: 260, height: 260 },
        rememberLastUsedCamera: true,
      },
      false,
    );

    this.scanner.render(
      (decodedText) => {
        void this.procesarQr(decodedText);
      },
      () => {},
    );
  }

  async procesarQr(decodedText: string): Promise<void> {
    if (!this.sesionActiva || this.procesandoQr) {
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

    this.procesandoQr = true;

    try {
      const registro = await this.asistenciasService.registrarQrEscaneado(
        codigoQr,
        this.nombresAlumnos,
      );
      this.resultadoQr = codigoQr;

      const existenteIdx = this.registros.findIndex((r) => r.alumnoId === registro.alumnoId);
      if (existenteIdx >= 0) {
        this.registros = this.registros.map((item, index) =>
          index === existenteIdx ? registro : item,
        );
        this.mensajeSesion = `${registro.nombre} actualizado: ${registro.estado}.`;
      } else {
        this.registros = [registro, ...this.registros];
        this.mensajeSesion = `${registro.nombre} registrado como ${
          registro.estado === 'PRESENTE' ? 'Presente' : 'Retardo'
        }.`;
      }
      void this.refrescarRegistrosDesdeServidor();
    } catch (error) {
      const mensaje = error instanceof Error ? error.message : 'No se pudo registrar el QR.';
      this.mensajeSesion = mensaje;
    } finally {
      this.procesandoQr = false;
    }
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

    if (!this.sesionId) {
      this.mensajeSesion = 'No hay sesión activa en el servidor.';
      return;
    }

    if (this.registros.length === 0) {
      this.mensajeSesion = 'No hay registros en esta sesión para confirmar.';
      return;
    }

    const confirmar = window.confirm(
      '¿Deseas confirmar esta lista de asistencia? Una vez confirmada no podrá modificarse aquí.',
    );
    if (!confirmar) {
      return;
    }

    this.listaConfirmada = true;
    this.sesionActiva = false;
    this.sesionFinalizada = true;
    this.detenerTemporizador();
    this.detenerScanner();
    this.mensajeSesion = 'Confirmando la lista...';

    try {
      if (!this.sesionFinalizada) {
        await this.asistenciasService.cerrarSesion(this.sesionId);
      }
      await this.asistenciasService.confirmarSesion(this.sesionId);
      if (this.materiaSeleccionada) {
        this.registros = await this.asistenciasService.sincronizarRegistrosSesion(
          this.sesionId,
          this.nombresAlumnos,
        );
      }
      this.mensajeSesion =
        `Lista confirmada (${this.registros.length} registro(s)). Descarga CSV o PDF abajo; tambi\u00e9n queda en el historial.`;
      if (this.materiaSeleccionada) {
        await this.cargarHistorialPases(this.materiaSeleccionada.id);
      }
    } catch (error) {
      this.listaConfirmada = false;
      this.mensajeSesion =
        error instanceof Error ? error.message : 'Error al confirmar la lista. Intenta nuevamente.';
    }
  }

  descargarListaCsv(): void {
    if (!this.materiaSeleccionada || !this.sesionId || this.registros.length === 0) {
      this.mensajeSesion = 'No hay registros para exportar.';
      return;
    }

    this.asistenciasService.descargarListaCsv(
      this.registros,
      this.contextoMateria(this.materiaSeleccionada),
      this.sesionId,
    );
    this.mensajeSesion = 'Archivo CSV descargado en tu equipo.';
  }

  descargarListaPdf(): void {
    if (!this.materiaSeleccionada || !this.sesionId || this.registros.length === 0) {
      this.mensajeSesion = 'No hay registros para exportar a PDF.';
      return;
    }

    this.asistenciasService.descargarListaPdf(
      this.registros,
      this.contextoMateria(this.materiaSeleccionada),
      this.sesionId,
    );
    this.mensajeSesion = 'PDF del pase de lista descargado.';
  }

  private async refrescarRegistrosDesdeServidor(): Promise<void> {
    if (!this.sesionId) {
      return;
    }
    try {
      this.registros = await this.asistenciasService.sincronizarRegistrosSesion(
        this.sesionId,
        this.nombresAlumnos,
      );
    } catch {
      // Mantener lista local si falla la sincronizaci\u00f3n.
    }
  }

  async solicitarReinicio(): Promise<void> {
    const confirmar = window.confirm(
      '\u00bfDeseas solicitar la lista de nuevo? Se invalidar\u00e1 la sesi\u00f3n actual.',
    );
    if (!confirmar) {
      return;
    }

    try {
      if (this.sesionId) {
        await this.asistenciasService.solicitarNuevaLista(this.sesionId);
      }
      this.sesionId = null;
      this.registros = [];
      this.listaConfirmada = false;
      await this.iniciarSesion();
      this.mensajeSesion = 'Nueva sesión iniciada. Escanea nuevamente los QR.';
    } catch (error) {
      this.mensajeSesion =
        error instanceof Error ? error.message : 'No se pudo reiniciar la sesión.';
    }
  }
}
