import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { TopbarAdmin } from "../../partials/topbar-admin/topbar-admin";
import { BottomNavbarAdmin } from "../../partials/bottom-navbar-admin/bottom-navbar-admin";

@Component({
  selector: 'app-dashboard-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarAdmin],
  templateUrl: './dashboard-screen.html',
  styleUrl: './dashboard-screen.scss'
})
export class DashboardScreen {

  estadisticas = [
    {
      icono: 'bi-people',
      titulo: 'TOTAL DE ALUMNOS',
      valor: '1,284',
      estado: '+4%',
      tipo: 'verde',
      color: 'azul'
    },
    {
      icono: 'bi-mortarboard',
      titulo: 'TOTAL DE DOCENTES',
      valor: '86',
      estado: 'Estable',
      tipo: 'gris',
      color: 'azul'
    },
    {
      icono: 'bi-journal-bookmark',
      titulo: 'MATERIAS ACTIVAS',
      valor: '42',
      estado: 'Activo',
      tipo: 'verde',
      color: 'naranja'
    },
    {
      icono: 'bi-calendar',
      titulo: 'PERIODOS ACTIVOS',
      valor: '2',
      estado: 'Finaliza hoy',
      tipo: 'rojo',
      color: 'gris'
    }
  ];

  actividades = [
    {
      icono: 'bi-person-plus',
      accion: 'Registro de Estudiante',
      usuario: 'Carlos Ortega',
      fecha: 'Hace 10 min',
      color: 'azul'
    },
    {
      icono: 'bi-list-check',
      accion: 'Modificación de Notas',
      usuario: 'Dra. María Lopez',
      fecha: 'Hace 1 h',
      color: 'negro'
    },
    {
      icono: 'bi-exclamation-triangle',
      accion: 'Error de Conexión API',
      usuario: 'Sistema Central',
      fecha: 'Hace 2 h',
      color: 'rojo'
    },
    {
      icono: 'bi-box-arrow-in-right',
      accion: 'Cierre de Periodo 2023-2',
      usuario: 'Dr. Smith',
      fecha: 'Ayer',
      color: 'negro'
    }
  ];

}