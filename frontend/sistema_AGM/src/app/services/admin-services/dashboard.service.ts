import { Injectable } from '@angular/core';
import { forkJoin, map, Observable, of, switchMap } from 'rxjs';

import { DocentesService } from './docentes.service';
import { MateriasService } from './materias.service';
import { PeriodoItem, PeriodosService } from './periodos.service';

export interface DashboardAction {
  label: string;
  route: string;
}

export interface DashboardActions {
  periodos: DashboardAction;
  docentes: DashboardAction;
  materias: DashboardAction;
}

export interface AdminDashboardResumen {
  totalPeriodos: number;
  periodoActivo: PeriodoItem | null;
  materiasPeriodoActivo: number;
  totalDocentes: number;
}

@Injectable({
  providedIn: 'root',
})
export class DashboardService {
  constructor(
    private periodos: PeriodosService,
    private materias: MateriasService,
    private docentes: DocentesService,
  ) {}

  getAcciones(): DashboardActions {
    return {
      periodos: { label: 'Ir a Periodos', route: '/admin/periodos' },
      docentes: { label: 'Ir a Docentes', route: '/admin/docentes' },
      materias: { label: 'Ir a Materias', route: '/admin/materias' },
    };
  }

  loadResumen(): Observable<AdminDashboardResumen> {
    return forkJoin({
      periodos: this.periodos.getPeriodos({ page: 1, pageSize: 1 }),
      periodoActivo: this.periodos.getPeriodoActivo(),
      docentes: this.docentes.getDocentes({ page: 1, pageSize: 1 }),
    }).pipe(
      switchMap(({ periodos, periodoActivo, docentes }) => {
        const materias$ = periodoActivo
          ? this.materias.countByPeriodo(periodoActivo.id)
          : of(0);

        return materias$.pipe(
          map((materiasPeriodoActivo) => ({
            totalPeriodos: periodos.count,
            periodoActivo,
            materiasPeriodoActivo,
            totalDocentes: docentes.count,
          })),
        );
      }),
    );
  }
}
