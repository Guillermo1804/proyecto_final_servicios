import { Injectable } from '@angular/core';
import { forkJoin, map, Observable, of, switchMap } from 'rxjs';

import { AlumnosService } from '../alumno-services/alumnos.service';
import { MateriaDocenteItem, MateriasDocenteService } from './materias-docente.service';

export interface DashboardClaseItem {
  hora: string;
  materia: string;
  grupo: string;
  nrc: string;
  materiaId: number;
  aula: string;
  icono: string;
  activo: boolean;
  alumnosInscritos: number;
}

export interface DashboardResumenMateriaItem {
  materia: string;
  grupo: string;
  nrc: string;
  materiaId: number;
  alumnosInscritos: number;
  estado: 'Activa' | 'Pendiente' | 'Terminado';
}

export interface DashboardDocenteData {
  periodoActivoNombre: string | null;
  clasesHoy: DashboardClaseItem[];
  resumenMaterias: DashboardResumenMateriaItem[];
  totalMateriasAsignadas: number;
  totalAlumnosInscritos: number;
  emptyMessage: string;
}

@Injectable({ providedIn: 'root' })
export class DashboardDocenteService {
  constructor(
    private materiasDocente: MateriasDocenteService,
    private alumnos: AlumnosService,
  ) {}

  loadDashboard(): Observable<DashboardDocenteData> {
    return this.materiasDocente.loadMateriasDocente().pipe(
      switchMap((load) => {
        const materias = load.materias;
        if (!materias.length) {
          return of({
            periodoActivoNombre: load.periodoActivoNombre,
            clasesHoy: [],
            resumenMaterias: [],
            totalMateriasAsignadas: 0,
            totalAlumnosInscritos: 0,
            emptyMessage: load.emptyMessage,
          });
        }

        const counts$ = materias.map((materia) =>
          this.alumnos.getAlumnosPorMateria(materia.id, 1, 1).pipe(
            map((page) => ({
              materia,
              alumnosInscritos: Number(page.count ?? page.results.length ?? 0),
            })),
          ),
        );

        return forkJoin(counts$).pipe(
          map((rows) => {
            const resumenMaterias: DashboardResumenMateriaItem[] = rows.map(
              ({ materia, alumnosInscritos }) => ({
                materia: materia.materia,
                grupo: materia.seccion || materia.clave,
                nrc: materia.nrc,
                materiaId: materia.id,
                alumnosInscritos,
                estado:
                  materia.estado === 'Activo'
                    ? 'Activa'
                    : materia.estado === 'Terminado'
                      ? 'Terminado'
                      : 'Pendiente',
              }),
            );

            const clasesHoy: DashboardClaseItem[] = rows.map(({ materia, alumnosInscritos }, index) => {
              const sesion = materia.sesiones[0];
              return {
                hora: sesion?.hora ?? '—',
                materia: materia.materia,
                grupo: `NRC ${materia.nrc} · ${materia.seccion || materia.clave}`,
                nrc: materia.nrc,
                materiaId: materia.id,
                aula: materia.salon,
                icono: index === 0 ? 'bi-broadcast' : 'bi-journal-bookmark',
                activo: index === 0,
                alumnosInscritos,
              };
            });

            const totalAlumnosInscritos = resumenMaterias.reduce(
              (sum, item) => sum + item.alumnosInscritos,
              0,
            );

            return {
              periodoActivoNombre: load.periodoActivoNombre,
              clasesHoy,
              resumenMaterias,
              totalMateriasAsignadas: materias.length,
              totalAlumnosInscritos,
              emptyMessage: '',
            };
          }),
        );
      }),
    );
  }
}
