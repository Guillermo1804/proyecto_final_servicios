import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, map, of, switchMap } from 'rxjs';

import { MateriaApiDto } from '../../models/periodos-api.model';
import { AlumnosService } from '../alumno-services/alumnos.service';
import { buildApiUrl, extractAgmListData, unwrapAgmData } from '../tools/agm-api.helpers';

export interface DetalleMateriaAlumnoItem {
  iniciales: string;
  nombre: string;
  matricula: string;
  asistencia: string;
}

export interface DetalleMateriaRubroItem {
  nombre: string;
  descripcion: string;
  porcentaje: number;
}

export interface DetalleMateriaActividadItem {
  titulo: string;
  descripcion: string;
  rubro: string;
  fechaEntrega: string;
  valorInterno: number;
  estado: string;
  tipo: string;
  entregas: number;
  calificaciones: Record<string, number>;
}

export interface DetalleMateriaResumenItem {
  grupo: string;
  materia: string;
  horario: string;
}

export interface DetalleMateriaActividadBaseItem {
  titulo: string;
  descripcion: string;
  rubro: string;
  fechaEntrega: string;
  estado: string;
  tipo: string;
  entregas: number;
}

@Injectable({
  providedIn: 'root'
})
export class DetalleMateriaDocenteService {
  private readonly materiasPath = 'materias';

  constructor(
    private alumnos: AlumnosService,
    private http: HttpClient,
  ) {}

  private readonly resumen: DetalleMateriaResumenItem = {
    grupo: 'ENG-302',
    materia: 'Cálculo Diferencial',
    horario: 'Lunes, Miércoles y Viernes | 08:00-10:00 AM'
  };

  /** Lista en memoria; use loadAlumnosPorNrc para datos MS-3. */
  private alumnosCargados: DetalleMateriaAlumnoItem[] = [];

  private readonly rubrosEvaluacion: DetalleMateriaRubroItem[] = [
    { nombre: 'Tareas', descripcion: 'Actividades y entregas semanales', porcentaje: 30 },
    { nombre: 'Proyecto', descripcion: 'Proyecto integrador de la materia', porcentaje: 30 },
    { nombre: 'Examen', descripcion: 'Evaluaciones parciales o finales', porcentaje: 40 }
  ];

  private readonly actividades: DetalleMateriaActividadItem[] = [
    {
      titulo: 'Tarea investigación',
      descripcion: 'Investigación sobre conceptos principales de la unidad.',
      rubro: 'Tareas',
      fechaEntrega: '2024-06-05',
      valorInterno: 40,
      estado: 'Abierta',
      tipo: 'abierta',
      entregas: 12,
      calificaciones: {
        '202300124': 92,
        '202300456': 85,
        '202300891': 78,
        '202300321': 95,
        '202300777': 88,
        '202300884': 83,
        '202300915': 90
      }
    },
    {
      titulo: 'Wireframes',
      descripcion: 'Diseño de pantallas principales del sistema.',
      rubro: 'Proyecto',
      fechaEntrega: '2024-06-12',
      valorInterno: 30,
      estado: 'En revisión',
      tipo: 'revision',
      entregas: 8,
      calificaciones: {
        '202300124': 88,
        '202300456': 90,
        '202300891': 80,
        '202300321': 94,
        '202300777': 86,
        '202300884': 79,
        '202300915': 92
      }
    },
    {
      titulo: 'Examen parcial',
      descripcion: 'Evaluación correspondiente al primer bloque temático.',
      rubro: 'Examen',
      fechaEntrega: '2024-06-18',
      valorInterno: 100,
      estado: 'Cerrada',
      tipo: 'cerrada',
      entregas: 32,
      calificaciones: {
        '202300124': 86,
        '202300456': 91,
        '202300891': 74,
        '202300321': 93,
        '202300777': 89,
        '202300884': 81,
        '202300915': 87
      }
    }
  ];

  loadResumenPorNrc(nrc: string): Observable<DetalleMateriaResumenItem> {
    const params = new HttpParams({ fromObject: { nrc, limit: '1', page: '1' } });
    return this.http.get<unknown>(buildApiUrl(`${this.materiasPath}/`), { params }).pipe(
      map((response) => {
        const data = unwrapAgmData<{ results?: MateriaApiDto[] }>(response);
        const list = Array.isArray(data?.results)
          ? data.results
          : extractAgmListData<MateriaApiDto>(response);
        const materia = list[0];
        if (!materia) {
          return { grupo: nrc, materia: 'Materia no encontrada', horario: '' };
        }
        return {
          grupo: materia.seccion,
          materia: materia.nombre,
          horario: String(materia.horario ?? ''),
        };
      }),
    );
  }

  loadAlumnosPorNrc(nrc: string): Observable<DetalleMateriaAlumnoItem[]> {
    return this.resolveMateriaIdByNrc(nrc).pipe(
      switchMap((materiaId) => {
        if (!materiaId) {
          return of([]);
        }
        return this.alumnos.getAlumnosPorMateria(materiaId, 1, 100).pipe(
          map((page) => {
            this.alumnosCargados = page.results.map((inscripcion) => {
              const alumno = inscripcion.alumno;
              const nombre = AlumnosService.mapAlumnoNombre(alumno);
              return {
                iniciales: AlumnosService.inicialesDesdeNombre(nombre),
                nombre,
                matricula: alumno.matricula,
                asistencia: '—',
              };
            });
            return this.alumnosCargados;
          }),
        );
      }),
    );
  }

  getResumen(): DetalleMateriaResumenItem {
    return { ...this.resumen };
  }

  /** @deprecated Usar loadAlumnosPorNrc */
  getAlumnos(): DetalleMateriaAlumnoItem[] {
    return this.alumnosCargados.map((alumno) => ({ ...alumno }));
  }

  private resolveMateriaIdByNrc(nrc: string): Observable<number | null> {
    const params = new HttpParams({ fromObject: { nrc, limit: '1', page: '1' } });
    return this.http.get<unknown>(buildApiUrl(`${this.materiasPath}/`), { params }).pipe(
      map((response) => {
        const data = unwrapAgmData<{ results?: MateriaApiDto[] }>(response);
        const list = Array.isArray(data?.results)
          ? data.results
          : extractAgmListData<MateriaApiDto>(response);
        return list[0] ? Number(list[0].id) : null;
      }),
    );
  }

  getRubrosEvaluacion(): DetalleMateriaRubroItem[] {
    return this.rubrosEvaluacion.map((rubro) => ({ ...rubro }));
  }

  getActividades(): DetalleMateriaActividadItem[] {
    return this.actividades.map((actividad) => ({
      ...actividad,
      calificaciones: { ...actividad.calificaciones }
    }));
  }

  crearActividadBase(): DetalleMateriaActividadBaseItem {
    return {
      titulo: '',
      descripcion: '',
      rubro: '',
      fechaEntrega: '',
      estado: 'Abierta',
      tipo: 'abierta',
      entregas: 0
    };
  }

  filtrarAlumnos(alumnos: DetalleMateriaAlumnoItem[], termino: string): DetalleMateriaAlumnoItem[] {
    const filtro = termino.trim().toLowerCase();

    if (!filtro) {
      return alumnos;
    }

    return alumnos.filter((alumno) =>
      [alumno.nombre, alumno.matricula, alumno.iniciales, alumno.asistencia]
        .join(' ')
        .toLowerCase()
        .includes(filtro)
    );
  }

  getTotalPaginas(totalItems: number, pageSize: number): number {
    return Math.max(1, Math.ceil(totalItems / Math.max(1, pageSize)));
  }

  paginar<T>(items: T[], pagina: number, pageSize: number): T[] {
    const paginaNormalizada = Math.max(1, pagina);
    const tamanoNormalizado = Math.max(1, pageSize);
    const inicio = (paginaNormalizada - 1) * tamanoNormalizado;

    return items.slice(inicio, inicio + tamanoNormalizado);
  }

  generarPaginas(totalPaginas: number): number[] {
    return Array.from({ length: Math.max(1, totalPaginas) }, (_, index) => index + 1);
  }

  getValorTotalRubros(rubros: DetalleMateriaRubroItem[]): number {
    return rubros.reduce((total, rubro) => total + Number(rubro.porcentaje), 0);
  }

  getValorTotalActividadesPorRubro(actividades: DetalleMateriaActividadItem[]): Record<string, number> {
    return actividades.reduce((acc, actividad) => {
      acc[actividad.rubro] = (acc[actividad.rubro] ?? 0) + Number(actividad.valorInterno);
      return acc;
    }, {} as Record<string, number>);
  }

  getMaximoRubro(rubros: DetalleMateriaRubroItem[], index: number): number {
    const sumaOtrosRubros = rubros.reduce((acc, rubro, currentIndex) => {
      if (currentIndex === index) {
        return acc;
      }

      return acc + Number(rubro.porcentaje);
    }, 0);

    return Math.max(0, 100 - sumaOtrosRubros);
  }

  limitarPorcentajeRubro(rubros: DetalleMateriaRubroItem[], index: number): void {
    const rubro = rubros[index];

    if (!rubro) {
      return;
    }

    const valor = Number(rubro.porcentaje);
    const maximoPermitido = this.getMaximoRubro(rubros, index);

    if (Number.isNaN(valor) || valor < 0) {
      rubro.porcentaje = 0;
      return;
    }

    if (valor > maximoPermitido) {
      rubro.porcentaje = maximoPermitido;
    }
  }

  recalcularValoresInternosTodosRubros(actividades: DetalleMateriaActividadItem[]): void {
    const rubros = [...new Set(actividades.map((actividad) => actividad.rubro))];

    for (const rubro of rubros) {
      this.recalcularValoresInternosRubro(actividades, rubro);
    }
  }

  recalcularValoresInternosRubro(actividades: DetalleMateriaActividadItem[], rubro: string): void {
    const actividadesRubro = actividades.filter((actividad) => actividad.rubro === rubro);

    if (!actividadesRubro.length) {
      return;
    }

    const base = Math.floor((100 / actividadesRubro.length) * 100) / 100;
    const acumuladoBase = base * actividadesRubro.length;
    const restante = Math.round((100 - acumuladoBase) * 100) / 100;

    actividadesRubro.forEach((actividad, index) => {
      actividad.valorInterno = index === actividadesRubro.length - 1
        ? Math.round((base + restante) * 100) / 100
        : base;
    });
  }

  getPesoActividad(
    actividad: { rubro: string; valorInterno: number },
    rubros: DetalleMateriaRubroItem[],
    totalActividadesPorRubro: Record<string, number>
  ): number {
    const rubro = rubros.find((item) => item.nombre === actividad.rubro);

    if (!rubro) {
      return 0;
    }

    const totalRubro = totalActividadesPorRubro[actividad.rubro] || 0;

    if (totalRubro <= 0) {
      return 0;
    }

    return (Number(rubro.porcentaje) * Number(actividad.valorInterno)) / totalRubro;
  }

  obtenerCalificacionActividad(actividad: { calificaciones?: Record<string, number> }, matricula: string): number {
    return actividad.calificaciones?.[matricula] ?? 0;
  }

  setCalificacionActividad(actividad: { calificaciones: Record<string, number> }, matricula: string, valor: number | string): number {
    const numero = Number(valor);
    const calificacion = Number.isNaN(numero) ? 0 : Math.round(Math.min(100, Math.max(0, numero)) * 100) / 100;
    actividad.calificaciones[matricula] = calificacion;

    return calificacion;
  }

  calcularPromedioAlumno(
    matricula: string,
    actividades: DetalleMateriaActividadItem[],
    rubros: DetalleMateriaRubroItem[]
  ): number {
    if (!actividades.length) {
      return 0;
    }

    const totalPeso = actividades.reduce(
      (suma, actividad) => suma + this.getPesoActividad(actividad, rubros, this.getValorTotalActividadesPorRubro(actividades)),
      0
    );

    if (totalPeso <= 0) {
      return 0;
    }

    const acumulado = actividades.reduce((suma, actividad) => {
      const peso = this.getPesoActividad(actividad, rubros, this.getValorTotalActividadesPorRubro(actividades));
      const nota = this.obtenerCalificacionActividad(actividad, matricula);

      return suma + (nota * peso);
    }, 0);

    return acumulado / totalPeso;
  }

  getPromedioPonderadoReal(
    alumnos: DetalleMateriaAlumnoItem[],
    actividades: DetalleMateriaActividadItem[],
    rubros: DetalleMateriaRubroItem[]
  ): number {
    if (!alumnos.length || !actividades.length) {
      return 0;
    }

    const totalPeso = actividades.reduce(
      (suma, actividad) => suma + this.getPesoActividad(actividad, rubros, this.getValorTotalActividadesPorRubro(actividades)),
      0
    );

    if (totalPeso <= 0) {
      return 0;
    }

    const promedioGeneral = alumnos.reduce((sumaAlumno, alumno) => {
      const promedioAlumno = actividades.reduce((sumaActividad, actividad) => {
        const peso = this.getPesoActividad(actividad, rubros, this.getValorTotalActividadesPorRubro(actividades));
        const calificacion = this.obtenerCalificacionActividad(actividad, alumno.matricula);

        return sumaActividad + (calificacion * peso);
      }, 0);

      return sumaAlumno + (promedioAlumno / totalPeso);
    }, 0);

    return promedioGeneral / alumnos.length;
  }

  getPromedioPonderadoRedondeado(
    alumnos: DetalleMateriaAlumnoItem[],
    actividades: DetalleMateriaActividadItem[],
    rubros: DetalleMateriaRubroItem[]
  ): number {
    return Math.floor(this.getPromedioPonderadoReal(alumnos, actividades, rubros) + 0.5);
  }

  getConcentradoCalificaciones(
    alumnos: DetalleMateriaAlumnoItem[],
    actividades: DetalleMateriaActividadItem[],
    rubros: DetalleMateriaRubroItem[]
  ): Array<DetalleMateriaAlumnoItem & { promedioReal: number; promedioRedondeado: number }> {
    return alumnos.map((alumno) => ({
      ...alumno,
      promedioReal: this.calcularPromedioAlumno(alumno.matricula, actividades, rubros),
      promedioRedondeado: Math.floor(this.calcularPromedioAlumno(alumno.matricula, actividades, rubros) + 0.5)
    }));
  }

  getPlanEvaluacionValido(rubros: DetalleMateriaRubroItem[]): boolean {
    return this.getValorTotalRubros(rubros) === 100;
  }

  crearActividadConCalificaciones(
    alumnos: DetalleMateriaAlumnoItem[],
    actividadBase: DetalleMateriaActividadBaseItem
  ): DetalleMateriaActividadItem {
    return {
      ...actividadBase,
      valorInterno: 0,
      calificaciones: alumnos.reduce((acc, alumno) => {
        acc[alumno.matricula] = 0;
        return acc;
      }, {} as Record<string, number>)
    };
  }
}