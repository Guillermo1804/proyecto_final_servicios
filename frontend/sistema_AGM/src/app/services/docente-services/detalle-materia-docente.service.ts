import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, catchError, forkJoin, map, of, switchMap } from 'rxjs';

import { InscripcionMateriaApiDto } from '../../models/alumnos-api.model';
import { ConcentradoMateriaDto } from '../../models/calificaciones-api.model';
import { MateriaApiDto } from '../../models/periodos-api.model';
import { AlumnosService } from '../alumno-services/alumnos.service';
import { CalificacionesService } from './calificaciones.service';
import { buildApiUrl, extractAgmListData, unwrapAgmData } from '../tools/agm-api.helpers';

export interface DetalleMateriaAlumnoItem {
  iniciales: string;
  nombre: string;
  matricula: string;
  email: string;
  asistencia: string;
  alumnoId?: number;
  usuarioId?: number | null;
  promedioReal?: number;
  promedioRedondeado?: number;
}

export interface DetalleMateriaRubroItem {
  nombre: string;
  descripcion: string;
  porcentaje: number;
  ponderacionId?: number;
}

export interface DetalleMateriaActividadItem {
  actividadId?: number;
  ponderacionId?: number;
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

export interface DetalleMateriaEvaluacionBundle {
  materiaId: number | null;
  rubros: DetalleMateriaRubroItem[];
  actividades: DetalleMateriaActividadItem[];
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
    private calificaciones: CalificacionesService,
    private http: HttpClient,
  ) {}

  /** Lista en memoria; use loadAlumnosPorNrc para datos MS-3. */
  private alumnosCargados: DetalleMateriaAlumnoItem[] = [];
  private materiaIdActual: number | null = null;

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
        return this.fetchAllInscripcionesPorMateria(materiaId).pipe(
          map((inscripciones) => {
            this.alumnosCargados = this.mapInscripcionesToAlumnos(inscripciones);
            return this.alumnosCargados;
          }),
        );
      }),
    );
  }

  private fetchAllInscripcionesPorMateria(
    materiaId: number,
    pageSize = 100,
  ): Observable<InscripcionMateriaApiDto[]> {
    return this.alumnos.getAlumnosPorMateria(materiaId, 1, pageSize).pipe(
      switchMap((firstPage) => {
        const acumulado = [...firstPage.results];
        const total = Number(firstPage.count ?? acumulado.length);
        const totalPaginas = Math.max(1, Math.ceil(total / pageSize));

        if (totalPaginas <= 1) {
          return of(acumulado);
        }

        const restantes = Array.from({ length: totalPaginas - 1 }, (_, index) =>
          this.alumnos.getAlumnosPorMateria(materiaId, index + 2, pageSize),
        );

        return forkJoin(restantes).pipe(
          map((paginas) => {
            for (const pagina of paginas) {
              acumulado.push(...pagina.results);
            }
            return acumulado;
          }),
        );
      }),
    );
  }

  private mapInscripcionesToAlumnos(
    inscripciones: InscripcionMateriaApiDto[],
  ): DetalleMateriaAlumnoItem[] {
    return inscripciones.map((inscripcion) => {
      const alumno = inscripcion.alumno;
      const nombre = AlumnosService.mapAlumnoNombre(alumno);
      return {
        iniciales: AlumnosService.inicialesDesdeNombre(nombre),
        nombre,
        matricula: alumno.matricula,
        email: String(alumno.email ?? '').trim() || '—',
        alumnoId: alumno.id,
        usuarioId: alumno.usuario_id ?? null,
        promedioRedondeado: 0,
        asistencia: '—',
      };
    });
  }

  /** @deprecated Usar loadAlumnosPorNrc */
  getAlumnos(): DetalleMateriaAlumnoItem[] {
    return this.alumnosCargados.map((alumno) => ({ ...alumno }));
  }

  getMateriaIdActual(): number | null {
    return this.materiaIdActual;
  }

  loadEvaluacionPorNrc(nrc: string): Observable<DetalleMateriaEvaluacionBundle> {
    return this.resolveMateriaIdByNrc(nrc).pipe(
      switchMap((materiaId) => {
        if (!materiaId) {
          return of({ materiaId: null, rubros: [], actividades: [] });
        }
        this.materiaIdActual = materiaId;
        return forkJoin({
          ponderaciones: this.calificaciones.getPonderaciones(materiaId).pipe(
            catchError(() => of({ materia_id: materiaId, ponderaciones: [], total: 0 })),
          ),
          actividades: this.calificaciones.getActividades(materiaId).pipe(
            catchError(() => of({ materia_id: materiaId, categorias: [] })),
          ),
          concentrado: this.calificaciones.getConcentrado(materiaId).pipe(
            catchError(() => of(null as ConcentradoMateriaDto | null)),
          ),
        }).pipe(
          map(({ ponderaciones, actividades, concentrado }) => {
            const rubros = ponderaciones.ponderaciones.map((pond) => ({
              ponderacionId: pond.id,
              nombre: pond.nombre_categoria,
              descripcion: '',
              porcentaje: Number(pond.porcentaje) || 0,
            }));
            const calificacionesPorActividad = this.mapCalificacionesDesdeConcentrado(concentrado);
            const items = this.mapActividadesDesdeApi(
              actividades.categorias,
              calificacionesPorActividad,
            );
            this.aplicarPromediosConcentrado(concentrado);
            this.recalcularValoresInternosTodosRubros(items);
            return { materiaId, rubros, actividades: items };
          }),
        );
      }),
    );
  }

  guardarPlanEvaluacion(
    materiaId: number,
    rubros: DetalleMateriaRubroItem[],
  ): Observable<DetalleMateriaRubroItem[]> {
    const ponderaciones = rubros
      .filter((rubro) => rubro.nombre.trim())
      .map((rubro) => ({
        nombre_categoria: rubro.nombre.trim(),
        porcentaje: Number(rubro.porcentaje) || 0,
      }));

    return this.calificaciones.savePonderaciones(materiaId, ponderaciones).pipe(
      map((data) =>
        data.ponderaciones.map((pond) => ({
          ponderacionId: pond.id,
          nombre: pond.nombre_categoria,
          descripcion: '',
          porcentaje: Number(pond.porcentaje) || 0,
        })),
      ),
    );
  }

  importarPlanEvaluacionExcel(materiaId: number, archivo: File): Observable<DetalleMateriaRubroItem[]> {
    return this.calificaciones.importPonderaciones(materiaId, archivo).pipe(
      map((data) =>
        data.ponderaciones.map((pond) => ({
          ponderacionId: pond.id,
          nombre: pond.nombre_categoria,
          descripcion: '',
          porcentaje: Number(pond.porcentaje) || 0,
        })),
      ),
    );
  }

  crearActividadRemota(
    rubros: DetalleMateriaRubroItem[],
    actividadBase: DetalleMateriaActividadBaseItem,
    alumnos: DetalleMateriaAlumnoItem[],
  ): Observable<DetalleMateriaActividadItem> {
    const rubro = rubros.find((item) => item.nombre === actividadBase.rubro);
    if (!rubro?.ponderacionId) {
      throw new Error('Guarda el plan de evaluacion antes de crear actividades en ese rubro.');
    }

    return this.calificaciones
      .createActividad({
        ponderacion_id: rubro.ponderacionId,
        nombre: actividadBase.titulo.trim(),
        descripcion: actividadBase.descripcion?.trim() || '',
        fecha: actividadBase.fechaEntrega || null,
      })
      .pipe(
        map((dto) => {
          const item: DetalleMateriaActividadItem = {
            actividadId: dto.id,
            ponderacionId: dto.ponderacion_id,
            titulo: dto.nombre,
            descripcion: dto.descripcion || '',
            rubro: dto.categoria_nombre,
            fechaEntrega: dto.fecha || '',
            valorInterno: 0,
            estado: actividadBase.estado,
            tipo: actividadBase.tipo,
            entregas: 0,
            calificaciones: alumnos.reduce(
              (acc, alumno) => {
                acc[alumno.matricula] = 0;
                return acc;
              },
              {} as Record<string, number>,
            ),
          };
          return item;
        }),
      );
  }

  persistirCalificacion(
    actividad: DetalleMateriaActividadItem,
    alumno: DetalleMateriaAlumnoItem,
    valor: number | string,
  ): Observable<number> {
    if (!actividad.actividadId || !alumno.alumnoId) {
      throw new Error('Faltan ids de actividad o alumno para guardar la calificacion.');
    }
    const calificacion = this.setCalificacionActividad(actividad, alumno.matricula, valor);
    return this.calificaciones
      .upsertCalificacion(actividad.actividadId, alumno.alumnoId, calificacion)
      .pipe(map(() => calificacion));
  }

  importarCalificacionesExcel(materiaId: number, archivo: File) {
    return this.calificaciones.importCalificaciones(materiaId, archivo);
  }

  cerrarMateriaCalificaciones(materiaId: number) {
    return this.calificaciones.cerrarMateria(materiaId);
  }

  marcarListaImpresa(materiaId: number) {
    return this.calificaciones.imprimirLista(materiaId);
  }

  recargarConcentrado(materiaId: number): Observable<DetalleMateriaAlumnoItem[]> {
    return this.calificaciones.getConcentrado(materiaId).pipe(
      map((concentrado) => {
        this.aplicarPromediosConcentrado(concentrado);
        return [...this.alumnosCargados];
      }),
    );
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
      [alumno.nombre, alumno.matricula, alumno.email, alumno.iniciales, alumno.asistencia]
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

  generarPaginasVentana(
    totalPaginas: number,
    paginaActual: number,
    maxVisible = 5,
  ): number[] {
    const total = Math.max(1, totalPaginas);
    if (total <= maxVisible) {
      return this.generarPaginas(total);
    }

    let inicio = Math.max(1, paginaActual - Math.floor(maxVisible / 2));
    let fin = inicio + maxVisible - 1;

    if (fin > total) {
      fin = total;
      inicio = fin - maxVisible + 1;
    }

    return Array.from({ length: fin - inicio + 1 }, (_, index) => inicio + index);
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
    const calificacion = Number.isNaN(numero)
      ? 0
      : Math.round(Math.min(10, Math.max(0, numero)) * 100) / 100;
    actividad.calificaciones[matricula] = calificacion;

    return calificacion;
  }

  private mapCalificacionesDesdeConcentrado(
    concentrado: ConcentradoMateriaDto | null,
  ): Record<number, Record<string, number>> {
    const map: Record<number, Record<string, number>> = {};
    if (!concentrado?.alumnos) {
      return map;
    }
    for (const alumno of concentrado.alumnos) {
      for (const item of alumno.calificaciones || []) {
        const actividadId = Number(item.actividad_id);
        if (!map[actividadId]) {
          map[actividadId] = {};
        }
        map[actividadId][alumno.matricula] = Number(item.calificacion) || 0;
      }
    }
    return map;
  }

  private mapActividadesDesdeApi(
    categorias: Array<{
      categoria_nombre: string;
      actividades: Array<{
        id: number;
        ponderacion_id: number;
        nombre: string;
        descripcion?: string;
        fecha?: string | null;
      }>;
    }>,
    calificacionesPorActividad: Record<number, Record<string, number>>,
  ): DetalleMateriaActividadItem[] {
    const items: DetalleMateriaActividadItem[] = [];
    for (const categoria of categorias) {
      for (const actividad of categoria.actividades || []) {
        items.push({
          actividadId: actividad.id,
          ponderacionId: actividad.ponderacion_id,
          titulo: actividad.nombre,
          descripcion: actividad.descripcion || '',
          rubro: categoria.categoria_nombre,
          fechaEntrega: actividad.fecha || '',
          valorInterno: 0,
          estado: 'Abierta',
          tipo: 'abierta',
          entregas: 0,
          calificaciones: { ...(calificacionesPorActividad[actividad.id] || {}) },
        });
      }
    }
    return items;
  }

  private aplicarPromediosConcentrado(concentrado: ConcentradoMateriaDto | null): void {
    if (!concentrado?.alumnos?.length) {
      return;
    }
    const porMatricula = new Map(
      concentrado.alumnos.map((alumno) => [alumno.matricula, alumno]),
    );
    this.alumnosCargados = this.alumnosCargados.map((alumno) => {
      const row = porMatricula.get(alumno.matricula);
      if (!row) {
        return alumno;
      }
      return {
        ...alumno,
        promedioReal: Number(row.promedio_real) || 0,
        promedioRedondeado: Number(row.promedio_redondeado) || 0,
      };
    });
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
    return alumnos.map((alumno) => {
      const promedioReal =
        alumno.promedioReal ??
        this.calcularPromedioAlumno(alumno.matricula, actividades, rubros);
      const promedioRedondeado =
        alumno.promedioRedondeado ??
        Math.floor(promedioReal + 0.5);
      return {
        ...alumno,
        promedioReal,
        promedioRedondeado,
      };
    });
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