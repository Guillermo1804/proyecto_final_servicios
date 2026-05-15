import { Routes } from '@angular/router';
import { LoginScreen } from './screens/login-screen/login-screen';
import { DashboardScreen } from './screens/admin-screen/dashboard-screen';
import { PeriodosScreen } from './screens/admin-screen/periodos-screen/periodos-screen';
import { MateriasScreen } from './screens/admin-screen/materias-screen/materias-screen';
import { DocentesScreen } from './screens/admin-screen/docentes-screen/docentes-screen';
import { DashboardScreen as DashboardDocenteScreen } from './screens/docente-screen/dashboard-screen/dashboard-screen';
import { MateriasScreen as MateriasDocenteScreen } from './screens/docente-screen/materias-screen/materias-screen';
import { DetalleMateriaScreen } from './screens/docente-screen/detalle-materia-screen/detalle-materia-screen';
import { CalificacionesScreen } from './screens/docente-screen/calificaciones-screen/calificaciones-screen';
import { AsistenciasScreen } from './screens/docente-screen/asistencias-screen/asistencias-screen';
import { ImportarAlumnosScreen } from './screens/docente-screen/importar-alumnos-screen/importar-alumnos-screen';
import { RendimientoScreen } from './screens/docente-screen/rendimiento-screen/rendimiento-screen';
import { ReportesScreen } from './screens/docente-screen/reportes-screen/reportes-screen';
import { DashboardScreen as DashboardAlumnoScreen } from './screens/alumno-screen/dashboard-screen/dashboard-screen';
import { HorarioScreen } from './screens/alumno-screen/horario-screen/horario-screen';
import { NotasScreen } from './screens/alumno-screen/notas-screen/notas-screen';
import { PerfilScreen } from './screens/alumno-screen/perfil-screen/perfil-screen';
export const routes: Routes = [
	{ path: '', component: LoginScreen },
	{ path: 'login', component: LoginScreen },
	{ path: 'admin/dashboard', component: DashboardScreen },
	{ path: 'admin/periodos', component: PeriodosScreen },
	{ path: 'admin/materias', component: MateriasScreen },
	{ path: 'admin/docentes', component: DocentesScreen },
	{ path: 'docente/dashboard', component: DashboardDocenteScreen },
	{ path: 'docente/materias', component: MateriasDocenteScreen },
	{ path: 'docente/materias/:id', component: DetalleMateriaScreen },
	{ path: 'docente/calificaciones', component: CalificacionesScreen },
	{ path: 'docente/asistencias', component: AsistenciasScreen },
    {path: 'docente/materias/:id/importar-alumnos', component: ImportarAlumnosScreen},
	{path: 'docente/materias/:id/rendimiento',component: RendimientoScreen},
	{path: 'docente/reportes', component: ReportesScreen},
	{path: 'alumno/dashboard', component: DashboardAlumnoScreen},
	{path: 'alumno/horario', component: HorarioScreen},
	{path: 'alumno/notas', component: NotasScreen},
	{path: 'alumno/perfil', component: PerfilScreen}
];
