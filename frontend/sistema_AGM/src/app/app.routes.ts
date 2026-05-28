import { Routes } from '@angular/router';
import { LoginScreen } from './screens/login-screen/login-screen';
import { ForgotPasswordScreen } from './screens/forgot-password-screen/forgot-password-screen';
import { ResetPasswordScreen } from './screens/reset-password-screen/reset-password-screen';
import { authGuard, roleGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'login' },

  { path: 'login', component: LoginScreen },
  { path: 'forgot-password', component: ForgotPasswordScreen },
  { path: 'reset-password', component: ResetPasswordScreen },

  {
    path: 'admin',
    canMatch: [authGuard, roleGuard],
    data: { roles: ['admin'] },
    loadChildren: () =>
      import('./screens/admin-screen/admin.routes').then((m) => m.ADMIN_ROUTES),
  },

  {
    path: 'docente',
    canMatch: [authGuard, roleGuard],
    data: { roles: ['docente'] },
    loadChildren: () =>
      import('./screens/docente-screen/docente.routes').then((m) => m.DOCENTE_ROUTES),
  },

  {
    path: 'alumno',
    canMatch: [authGuard, roleGuard],
    data: { roles: ['alumno'] },
    loadChildren: () =>
      import('./screens/alumno-screen/alumno.routes').then((m) => m.ALUMNO_ROUTES),
  },

  { path: '**', redirectTo: 'login' },
];
