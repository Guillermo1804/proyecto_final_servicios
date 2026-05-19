import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarAdmin } from '../../../partials/bottom-navbar-admin/bottom-navbar-admin';
import { FacadeService } from '../../../services/facade.service';

interface MateriaCard {
  codigo: string;
  nombre: string;
  prerequisito: string;
  facultad: string;
  tipo: string;
}

@Component({
  selector: 'app-materias-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarAdmin],
  templateUrl: './materias-screen.html',
  styleUrl: './materias-screen.scss',
})
export class MateriasScreen implements OnInit {
  materias: MateriaCard[] = [];
  loading = true;
  errorMessage = '';

  constructor(private facade: FacadeService) {}

  ngOnInit(): void {
    this.facade.listMaterias({ limit: 100 }).subscribe({
      next: (body) => {
        this.loading = false;
        const rows = this.facade.extractList<{
          nrc?: string;
          clave?: string;
          nombre?: string;
          seccion?: string;
        }>(body);
        this.materias = rows.map((m) => ({
          codigo: m.nrc || m.clave || '—',
          nombre: m.nombre ?? '—',
          prerequisito: m.seccion ? `Sección ${m.seccion}` : '—',
          facultad: 'AGM',
          tipo: 'ingenieria',
        }));
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No se pudieron cargar las materias.';
      },
    });
  }
}
