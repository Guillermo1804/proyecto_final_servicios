import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { FacadeService } from './facade.service';

const AUTH_EXCLUDED_PATTERNS = [
  '/auth/login',
  '/auth/logout',
  '/auth/refresh-token',
  '/auth/forgot-password',
  '/auth/reset-password',
];

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  if (AUTH_EXCLUDED_PATTERNS.some((pattern) => request.url.includes(pattern))) {
    return next(request);
  }

  const facadeService = inject(FacadeService);
  const token = facadeService.getAccessToken();

  if (!token) {
    return next(request);
  }

  return next(
    request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    })
  );
};