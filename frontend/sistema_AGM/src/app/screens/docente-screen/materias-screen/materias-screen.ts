import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { RouterLink } from '@angular/router';
import { TopbarAdmin } from "../../../partials/topbar-admin/topbar-admin";
import { MateriaDocenteItem, MateriasDocenteService } from '../../../services/docente-services/materias-docente.service';

@Component({
  selector: 'app-materias-docente-screen',
  standalone: true,
  imports: [CommonModule, BottomNavbarDocente, RouterLink, TopbarAdmin],
  templateUrl: './materias-screen.html',
  styleUrl: './materias-screen.scss'
})
export class MateriasScreen implements OnInit {

  materias: MateriaDocenteItem[] = [];
  private readonly materiasService = inject(MateriasDocenteService);

  ngOnInit(): void {
    this.materiasService.getMaterias().subscribe((materias) => {
      this.materias = materias;
    });
  }

  trackByMateria(_: number, materia: { nrc: string }): string {
    return materia.nrc;
  }

}