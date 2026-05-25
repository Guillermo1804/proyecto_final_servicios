import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { MateriasDocenteService } from '../../../services/docente-services/materias-docente.service';

@Component({
  selector: 'app-calificaciones-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente, RouterLink],
  templateUrl: './calificaciones-screen.html',
  styleUrl: './calificaciones-screen.scss',
})
export class CalificacionesScreen implements OnInit {
  materias: { nrc: string; nombre: string }[] = [];
  isLoading = true;
  emptyMessage = '';

  constructor(private materiasDocente: MateriasDocenteService) {}

  ngOnInit(): void {
    this.materiasDocente
      .loadMateriasDocente()
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (result) => {
          this.materias = result.materias.map((m) => ({
            nrc: m.nrc,
            nombre: m.materia,
          }));
          this.emptyMessage = result.emptyMessage;
        },
        error: () => {
          this.emptyMessage = 'No se pudieron cargar tus materias.';
        },
      });
  }
}
