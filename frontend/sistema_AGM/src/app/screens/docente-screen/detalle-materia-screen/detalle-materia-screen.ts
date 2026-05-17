import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
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
export class DetalleMateriaScreen implements OnInit {

  ngOnInit(): void {
    // Aquí podrías cargar los datos de la materia usando el código obtenido de la ruta
    // Ejemplo: this.materiaService.getMateria(this.codigoMateria).subscribe(...)
  }
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
    nombre: 'Tareas',
    descripcion: 'Actividades y entregas semanales',
    porcentaje: 30
  },
  {
    nombre: 'Proyecto',
    descripcion: 'Proyecto integrador de la materia',
    porcentaje: 30
  },
  {
    nombre: 'Examen',
    descripcion: 'Evaluaciones parciales o finales',
    porcentaje: 40
  }
];

actividades = [
  {
    titulo: 'Tarea investigación',
    descripcion: 'Investigación sobre conceptos principales de la unidad.',
    rubro: 'Tareas',
    fechaEntrega: '2024-06-05',
    valorInterno: 40,
    estado: 'Abierta',
    tipo: 'abierta',
    entregas: 12
  },
  {
    titulo: 'Wireframes',
    descripcion: 'Diseño de pantallas principales del sistema.',
    rubro: 'Proyecto',
    fechaEntrega: '2024-06-12',
    valorInterno: 30,
    estado: 'En revisión',
    tipo: 'revision',
    entregas: 8
  },
  {
    titulo: 'Examen parcial',
    descripcion: 'Evaluación correspondiente al primer bloque temático.',
    rubro: 'Examen',
    fechaEntrega: '2024-06-18',
    valorInterno: 100,
    estado: 'Cerrada',
    tipo: 'cerrada',
    entregas: 32
  }
];

nuevaActividad = {
  titulo: '',
  descripcion: '',
  rubro: '',
  fechaEntrega: '',
  valorInterno: 0,
  estado: 'Abierta',
  tipo: 'abierta',
  entregas: 0
};

mostrarFormularioActividad = false;

abrirFormularioActividad(): void {
  this.mostrarFormularioActividad = true;
}

cancelarActividad(): void {
  this.mostrarFormularioActividad = false;

  this.nuevaActividad = {
    titulo: '',
    descripcion: '',
    rubro: '',
    fechaEntrega: '',
    valorInterno: 0,
    estado: 'Abierta',
    tipo: 'abierta',
    entregas: 0
  };
}

crearActividad(): void {
  if (!this.nuevaActividad.titulo || !this.nuevaActividad.rubro) {
    alert('Completa el nombre de la actividad y el rubro.');
    return;
  }

  this.actividades.push({ ...this.nuevaActividad });

  this.cancelarActividad();
}

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