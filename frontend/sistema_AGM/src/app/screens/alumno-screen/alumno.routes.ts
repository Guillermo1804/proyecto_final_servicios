import { Routes } from '@angular/router';
import { DashboardScreen } from './dashboard-screen/dashboard-screen';
import { HorarioScreen } from './horario-screen/horario-screen';
import { NotasScreen } from './notas-screen/notas-screen';
import { PerfilScreen } from './perfil-screen/perfil-screen';
import { QrAsistenciaScreen } from './qr-asistencia-screen/qr-asistencia-screen';

export const ALUMNO_ROUTES: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
  { path: 'dashboard', component: DashboardScreen },
  { path: 'horario', component: HorarioScreen },
  { path: 'qr', component: QrAsistenciaScreen },
  { path: 'notas', component: NotasScreen },
  { path: 'perfil', component: PerfilScreen }
];