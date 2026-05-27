import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { RouterLink } from '@angular/router';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import {
  MateriaDocenteItem,
  MateriasDocenteService,
} from '../../../services/docente-services/materias-docente.service';
import { finalize } from 'rxjs';

@Component({
  selector: 'app-materias-docente-screen',
  standalone: true,
  imports: [CommonModule, BottomNavbarDocente, RouterLink, TopbarAdmin],
  templateUrl: './materias-screen.html',
  styleUrl: './materias-screen.scss',
})
export class MateriasScreen implements OnInit {
  materias: MateriaDocenteItem[] = [];
  periodoActivoNombre: string | null = null;
  isLoading = true;
  emptyMessage = '';

  private readonly materiasService = inject(MateriasDocenteService);

  ngOnInit(): void {
    this.materiasService
      .loadMateriasDocente()
      .pipe(finalize(() => {
        this.isLoading = false;
      }))
      .subscribe({
        next: (result) => {
          this.periodoActivoNombre = result.periodoActivoNombre;
          this.materias = result.materias;
          this.emptyMessage = result.emptyMessage;
        },
        error: () => {
          this.emptyMessage = 'Error al cargar tus materias. Verifica que MS-2 y MS-3 esten en marcha.';
          this.materias = [];
        },
      });
  }

  trackByMateria(_: number, materia: { nrc: string }): string {
    return materia.nrc;
  }
}
