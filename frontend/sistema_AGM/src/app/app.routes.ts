import { Routes } from '@angular/router';
import { LoginScreen } from './screens/login-screen/login-screen';
export const routes: Routes = [
	{ path: '', pathMatch: 'full', redirectTo: 'login' },
	{ path: 'login', component: LoginScreen },
	{ path: 'admin', loadChildren: () => import('./screens/admin-screen/admin.routes').then((routes) => routes.ADMIN_ROUTES) },
	{ path: 'docente', loadChildren: () => import('./screens/docente-screen/docente.routes').then((routes) => routes.DOCENTE_ROUTES) },
	{ path: 'alumno', loadChildren: () => import('./screens/alumno-screen/alumno.routes').then((routes) => routes.ALUMNO_ROUTES) },
	{ path: '**', redirectTo: 'login' }
];
