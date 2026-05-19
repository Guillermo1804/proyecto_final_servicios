import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { RouterLink } from '@angular/router';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { FacadeService } from '../../../services/facade.service';

@Component({
  selector: 'app-materias-docente-screen',
  standalone: true,
  imports: [CommonModule, BottomNavbarDocente, RouterLink, TopbarAdmin],
  templateUrl: './materias-screen.html',
  styleUrl: './materias-screen.scss',
})
export class MateriasScreen implements OnInit {
  materias: Array<{
    id: number;
    codigo: string;
    nombre: string;
    facultad: string;
    alumnos: number;
    progreso: number;
    horario: string;
  }> = [];
  loading = true;
  errorMessage = '';

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    const docenteId = this.facade.getUserId();
    this.facade.listMaterias({ limit: 200 }).subscribe({
      next: (body) => {
        this.loading = false;
        const rows = this.facade.extractList<{
          id?: number;
          nrc?: string;
          nombre?: string;
          docente_id?: number;
          horario?: string;
        }>(body);
        const filtered =
          docenteId != null
            ? rows.filter((m) => m.docente_id === docenteId)
            : rows;
        this.materias = filtered.map((m) => ({
          id: m.id ?? 0,
          codigo: m.nrc ?? '—',
          nombre: m.nombre ?? '—',
          facultad: 'Facultad de Ciencias',
          alumnos: 0,
          progreso: 0,
          horario: m.horario ?? '—',
        }));
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudieron cargar tus materias.';
      },
    });
  }
}
