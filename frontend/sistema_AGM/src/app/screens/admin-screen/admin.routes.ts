import { Routes } from '@angular/router';
import { DashboardScreen } from './dashboard-screen';
import { PeriodosScreen } from './periodos-screen/periodos-screen';
import { MateriasScreen } from './materias-screen/materias-screen';
import { DocentesScreen } from './docentes-screen/docentes-screen';

export const ADMIN_ROUTES: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
  { path: 'dashboard', component: DashboardScreen },
  { path: 'periodos', component: PeriodosScreen },
  { path: 'materias', component: MateriasScreen },
  { path: 'docentes', component: DocentesScreen }
];