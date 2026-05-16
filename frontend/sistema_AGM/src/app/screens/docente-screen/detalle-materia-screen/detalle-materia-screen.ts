import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
@Component({
  selector: 'app-detalle-materia-screen',
  standalone: true,
  imports: [CommonModule, BottomNavbarDocente, TopbarAdmin,RouterLink,FormsModule],
  templateUrl: './detalle-materia-screen.html',
  styleUrl: './detalle-materia-screen.scss'
})
export class DetalleMateriaScreen {

  codigoMateria = '';

  alumnos = [
    {
      iniciales: 'AG',
      nombre: 'Alonso García, Roberto',
      matricula: '202300124',
      asistencia: '98%'
    },
    {
      iniciales: 'BC',
      nombre: 'Barrera Cruz, Sofía',
      matricula: '202300456',
      asistencia: '85%'
    },
    {
      iniciales: 'DV',
      nombre: 'Díaz Valdés, Marco',
      matricula: '202300891',
      asistencia: '62%'
    },
    {
      iniciales: 'LM',
      nombre: 'López Mora, Elena',
      matricula: '202300321',
      asistencia: '100%'
    }
  ];

  constructor(private route: ActivatedRoute) {
    this.codigoMateria = this.route.snapshot.paramMap.get('id') ?? '';
  }

  tabActiva: 'alumnos' | 'evaluacion' | 'actividades' = 'alumnos';

cambiarTab(tab: 'alumnos' | 'evaluacion' | 'actividades'): void {
  this.tabActiva = tab;
}
rubrosEvaluacion = [
  {
    nombre: 'Parcial 1',
    descripcion: 'Examen teórico y ejercicios prácticos',
    porcentaje: 20
  },
  {
    nombre: 'Parcial 2',
    descripcion: 'Proyecto aplicado y resolución de problemas',
    porcentaje: 30
  },
  {
    nombre: 'Evaluación Final',
    descripcion: 'Examen final acumulativo',
    porcentaje: 50
  }
];

get totalEvaluacion(): number {
  return this.rubrosEvaluacion.reduce(
    (acc, item) => acc + Number(item.porcentaje),
    0
  );
}

agregarRubro(): void {

  this.rubrosEvaluacion.push({
    nombre: '',
    descripcion: '',
    porcentaje: 0
  });

}

eliminarRubro(index: number): void {
  this.rubrosEvaluacion.splice(index, 1);
}
guardarPlanEvaluacion(): void {
  if (this.totalEvaluacion !== 100) {
    alert('El total debe ser exactamente 100%');
    return;
  }

  const payload = {
    materia: this.codigoMateria,
    rubros: this.rubrosEvaluacion
  };

  console.log('Datos para backend:', payload);

  // después:
  // this.materiaService.guardarPlanEvaluacion(payload).subscribe(...)
}
}