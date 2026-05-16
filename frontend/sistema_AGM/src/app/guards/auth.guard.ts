import { inject } from '@angular/core';
import { CanMatchFn, Route, Router, UrlSegment } from '@angular/router';
import { FacadeService } from '../services/facade.service';

function getAllowedRoles(route: Route): string[] {
  const roles = route.data?.['roles'];

  if (!Array.isArray(roles)) {
    return [];
  }

  return roles.map((role) => String(role).toLowerCase());
}

export const authGuard: CanMatchFn = () => {
  const facadeService = inject(FacadeService);
  const router = inject(Router);

  if (facadeService.isAuthenticated()) {
    return true;
  }

  return router.createUrlTree(['/login']);
};

export const roleGuard: CanMatchFn = (route: Route, _segments: UrlSegment[]) => {
  const facadeService = inject(FacadeService);
  const router = inject(Router);
  const allowedRoles = getAllowedRoles(route);

  if (!facadeService.isAuthenticated()) {
    return router.createUrlTree(['/login']);
  }

  if (allowedRoles.length === 0) {
    return true;
  }

  const userRole = facadeService.getUserRole();

  if (userRole && allowedRoles.includes(userRole.toLowerCase())) {
    return true;
  }

  return router.createUrlTree([facadeService.resolveHomeRoute(userRole)]);
};