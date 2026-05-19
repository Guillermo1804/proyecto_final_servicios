import { Routes } from '@angular/router';
import { LoginScreen } from './screens/login-screen/login-screen';
import { authGuard, roleGuard } from './guards/auth.guard';
export const routes: Routes = [
	{ path: '', pathMatch: 'full', redirectTo: 'login' },
	{ path: 'login', component: LoginScreen },
	{
		path: 'forgot-password',
		loadComponent: () =>
			import('./screens/forgot-password-screen/forgot-password-screen').then(
				(m) => m.ForgotPasswordScreen,
			),
	},
	{
		path: 'reset-password',
		loadComponent: () =>
			import('./screens/reset-password-screen/reset-password-screen').then(
				(m) => m.ResetPasswordScreen,
			),
	},
	{ path: 'admin', canMatch: [authGuard, roleGuard], data: { roles: ['admin'] }, loadChildren: () => import('./screens/admin-screen/admin.routes').then((routes) => routes.ADMIN_ROUTES) },
	{ path: 'docente', canMatch: [authGuard, roleGuard], data: { roles: ['docente'] }, loadChildren: () => import('./screens/docente-screen/docente.routes').then((routes) => routes.DOCENTE_ROUTES) },
	{ path: 'alumno', canMatch: [authGuard, roleGuard], data: { roles: ['alumno'] }, loadChildren: () => import('./screens/alumno-screen/alumno.routes').then((routes) => routes.ALUMNO_ROUTES) },
	{ path: '**', redirectTo: 'login' }
];
