import { Routes } from '@angular/router';
import { DashboardScreen } from './dashboard-screen/dashboard-screen';
import { MateriasScreen } from './materias-screen/materias-screen';
import { DetalleMateriaScreen } from './detalle-materia-screen/detalle-materia-screen';
import { CalificacionesScreen } from './calificaciones-screen/calificaciones-screen';
import { AsistenciasScreen } from './asistencias-screen/asistencias-screen';
import { ImportarAlumnosScreen } from './importar-alumnos-screen/importar-alumnos-screen';
import { RendimientoScreen } from './rendimiento-screen/rendimiento-screen';
import { ReportesScreen } from './reportes-screen/reportes-screen';

export const DOCENTE_ROUTES: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
  { path: 'dashboard', component: DashboardScreen },
  { path: 'materias', component: MateriasScreen },
  { path: 'materias/:id', component: DetalleMateriaScreen },
  { path: 'calificaciones', component: CalificacionesScreen },
  { path: 'asistencias', component: AsistenciasScreen },
  { path: 'materias/:id/importar-alumnos', component: ImportarAlumnosScreen },
  { path: 'materias/:id/rendimiento', component: RendimientoScreen },
  { path: 'reportes', component: ReportesScreen }
];