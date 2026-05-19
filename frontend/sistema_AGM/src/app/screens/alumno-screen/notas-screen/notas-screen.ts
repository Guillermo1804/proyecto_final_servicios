import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';
import { FacadeService } from '../../../services/facade.service';

@Component({
  selector: 'app-notas-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarAlumno],
  templateUrl: './notas-screen.html',
  styleUrl: './notas-screen.scss',
})
export class NotasScreen implements OnInit {
  materias: Array<{
    icono: string;
    color: string;
    nombre: string;
    nrc: string;
    profesor: string;
    promedio: number;
    promedioColor: string;
    expandido: boolean;
    parciales: Array<{ titulo: string; valor: string; activo?: boolean }>;
  }> = [];
  historial: Array<{ periodo: string; materias: number; aprobadas: number }> = [];
  loading = true;
  errorMessage = '';

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    this.facade.getMisMateriasAlumno().subscribe({
      next: (body) => {
        this.loading = false;
        const rows = this.facade.extractList<{
          materia_id?: number;
          materia_detail?: { nombre?: string; nrc?: string; docente_nombre?: string };
        }>(body);
        this.materias = rows.map((row, idx) => ({
          icono: 'bi-book',
          color: ['azul', 'naranja', 'morado', 'gris'][idx % 4],
          nombre: row.materia_detail?.nombre ?? `Materia ${row.materia_id}`,
          nrc: row.materia_detail?.nrc ?? '—',
          profesor: row.materia_detail?.docente_nombre ?? '—',
          promedio: 0,
          promedioColor: 'gris',
          expandido: idx === 0,
          parciales: [{ titulo: 'Promedio', valor: '--', activo: true }],
        }));
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudieron cargar tus materias.';
      },
    });
  }
}
