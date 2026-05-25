import { inject } from '@angular/core';
import { CanMatchFn, Route, Router, UrlSegment } from '@angular/router';

import { AuthService } from '../services/auth.service';

function getAllowedRoles(route: Route): string[] {
  const roles = route.data?.['roles'];
  if (!Array.isArray(roles)) {
    return [];
  }
  return roles.map((role) => String(role).toLowerCase());
}

export const authGuard: CanMatchFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated()) {
    return true;
  }
  return router.createUrlTree(['/login']);
};

export const roleGuard: CanMatchFn = (route: Route, _segments: UrlSegment[]) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const allowedRoles = getAllowedRoles(route);

  if (!auth.isAuthenticated()) {
    return router.createUrlTree(['/login']);
  }

  if (allowedRoles.length === 0) {
    return true;
  }

  const userRole = auth.getUserRole();
  if (userRole && allowedRoles.includes(userRole)) {
    return true;
  }

  return router.createUrlTree([auth.resolveHomeRoute(userRole)]);
};
