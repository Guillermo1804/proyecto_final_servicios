import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAlumno } from '../../../partials/bottom-navbar-alumno/bottom-navbar-alumno';
import { FacadeService } from '../../../services/facade.service';

@Component({
  selector: 'app-horario-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarAlumno],
  templateUrl: './horario-screen.html',
  styleUrl: './horario-screen.scss',
})
export class HorarioScreen implements OnInit {
  horarios: Array<{ hora: string; materia: string; aula: string; color: string }> = [];
  loading = true;

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    this.facade.getMisMateriasAlumno().subscribe({
      next: (body) => {
        this.loading = false;
        const rows = this.facade.extractList<{
          materia_detail?: { nombre?: string; horario?: string };
        }>(body);
        this.horarios = rows.map((row, idx) => ({
          hora: '—',
          materia: row.materia_detail?.nombre ?? 'Materia',
          aula: row.materia_detail?.horario ?? 'Por definir',
          color: ['blue', 'green', 'orange', 'purple'][idx % 4],
        }));
      },
      error: () => {
        this.loading = false;
      },
    });
  }
}
