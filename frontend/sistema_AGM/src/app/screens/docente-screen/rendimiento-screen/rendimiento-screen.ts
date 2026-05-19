import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { TopbarAdmin } from '../../../partials/topbar-admin/topbar-admin';
import { BottomNavbarDocente } from '../../../partials/bottom-navbar-docente/bottom-navbar-docente';
import { FacadeService } from '../../../services/facade.service';

interface EstudianteRiesgo {
  iniciales: string;
  nombre: string;
  matricula: string;
  promedio: string;
  asistencia: string;
}

@Component({
  selector: 'app-rendimiento-screen',
  standalone: true,
  imports: [CommonModule, TopbarAdmin, BottomNavbarDocente],
  templateUrl: './rendimiento-screen.html',
  styleUrl: './rendimiento-screen.scss',
})
export class RendimientoScreen implements OnInit {
  materiaId = 0;
  nombreMateria = '';
  promedioGrupo = '—';
  estudiantesRiesgo: EstudianteRiesgo[] = [];
  distribucion: Array<{ rango: string; count: number; pct: number }> = [];
  loading = true;
  errorMessage = '';
  ultimaActualizacion = '';

  constructor(
    private route: ActivatedRoute,
    private facade: FacadeService,
  ) {}

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    this.materiaId = idParam ? Number(idParam) : 0;
    if (!this.materiaId) {
      this.loading = false;
      this.errorMessage = 'Materia no válida.';
      return;
    }

    const uid = this.facade.getUserId();
    if (uid) {
      this.facade.listMateriasDocente(uid).subscribe({
        next: (body) => {
          const m = this.facade
            .extractList<{ id?: number; nombre?: string }>(body)
            .find((row) => row.id === this.materiaId);
          if (m?.nombre) {
            this.nombreMateria = m.nombre;
          }
        },
      });
    }

    this.facade.getConcentrado(this.materiaId).subscribe({
      next: (body) => {
        this.loading = false;
        this.ultimaActualizacion = new Date().toLocaleString('es-MX');
        const data = body?.data as {
          alumnos?: {
            matricula?: string;
            nombre?: string;
            promedio_real?: string;
            promedio_redondeado?: number;
          }[];
        };
        const alumnos = data?.alumnos ?? [];
        if (!alumnos.length) {
          this.errorMessage = 'Sin concentrado para esta materia.';
          return;
        }

        const proms = alumnos
          .map((a) => parseFloat(a.promedio_real ?? ''))
          .filter((n) => !Number.isNaN(n));
        if (proms.length) {
          this.promedioGrupo = (proms.reduce((a, b) => a + b, 0) / proms.length).toFixed(1);
        }

        const buckets = [0, 0, 0, 0, 0];
        alumnos.forEach((a) => {
          const n = parseFloat(a.promedio_real ?? '0');
          if (n < 6) buckets[0]++;
          else if (n < 7) buckets[1]++;
          else if (n < 8) buckets[2]++;
          else if (n < 9) buckets[3]++;
          else buckets[4]++;
        });
        const total = alumnos.length || 1;
        this.distribucion = [
          { rango: '0-5.9', count: buckets[0], pct: Math.round((buckets[0] / total) * 100) },
          { rango: '6-6.9', count: buckets[1], pct: Math.round((buckets[1] / total) * 100) },
          { rango: '7-7.9', count: buckets[2], pct: Math.round((buckets[2] / total) * 100) },
          { rango: '8-8.9', count: buckets[3], pct: Math.round((buckets[3] / total) * 100) },
          { rango: '9-10', count: buckets[4], pct: Math.round((buckets[4] / total) * 100) },
        ];

        this.estudiantesRiesgo = alumnos
          .filter((a) => (a.promedio_redondeado ?? 10) < 6)
          .map((a) => ({
            iniciales: this.iniciales(a.nombre ?? '?'),
            nombre: a.nombre ?? '—',
            matricula: a.matricula ?? '—',
            promedio: a.promedio_real ?? String(a.promedio_redondeado ?? '—'),
            asistencia: '—',
          }));
      },
      error: () => {
        this.loading = false;
        this.errorMessage =
          'No hay concentrado para esta materia (configure ponderaciones y actividades).';
      },
    });
  }

  private iniciales(nombre: string): string {
    const parts = nombre.trim().split(/\s+/).filter(Boolean);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return nombre.slice(0, 2).toUpperCase();
  }
}
