import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { AfterViewInit, OnDestroy } from '@angular/core';
import { Html5QrcodeScanner } from 'html5-qrcode';

@Component({
  selector: 'app-asistencias-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './asistencias-screen.html',
  styleUrl: './asistencias-screen.scss'
})
export class AsistenciasScreen implements OnDestroy {
registros = [
  {
    foto: '/assets/alumno1.jpg',
    nombre: 'Martínez, Ana Lucía',
    hora: '14:02:15',
    estado: 'PUNTUAL',
    tipo: 'puntual'
  },
  {
    foto: '/assets/alumno2.jpg',
    nombre: 'García Ruiz, Carlos',
    hora: '14:03:42',
    estado: 'PUNTUAL',
    tipo: 'puntual'
  }
];
  modo: 'codigo' | 'scanner' = 'codigo';
  scanner: Html5QrcodeScanner | null = null;
  resultadoQr = '';

  cambiarModo(modo: 'codigo' | 'scanner'): void {
    this.modo = modo;

    if (modo === 'scanner') {
      setTimeout(() => this.iniciarScanner(), 100);
    } else {
      this.detenerScanner();
    }
  }

  iniciarScanner(): void {
    if (this.scanner) return;

    this.scanner = new Html5QrcodeScanner(
      'reader',
      {
        fps: 10,
        qrbox: 250
      },
      false
    );

    this.scanner.render(
      (decodedText) => {
        this.resultadoQr = decodedText;
        console.log('QR detectado:', decodedText);
      },
      () => {}
    );
  }

  detenerScanner(): void {
    if (this.scanner) {
      this.scanner.clear();
      this.scanner = null;
    }
  }

  ngOnDestroy(): void {
    this.detenerScanner();
  }

}