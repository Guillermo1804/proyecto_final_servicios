import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';
import { FacadeService } from './facade.service';

const AUTH_EXCLUDED_PATTERNS = [
  '/auth/login',
  '/auth/logout',
  '/auth/refresh-token',
  '/auth/forgot-password',
  '/auth/reset-password',
];

function isAuthExcluded(url: string): boolean {
  return AUTH_EXCLUDED_PATTERNS.some((pattern) => url.includes(pattern));
}

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const facadeService = inject(FacadeService);
  const router = inject(Router);

  let req = request;
  if (!isAuthExcluded(request.url)) {
    const token = facadeService.getAccessToken();
    if (token) {
      req = request.clone({
        setHeaders: { Authorization: `Bearer ${token}` },
      });
    }
  }

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (
        error.status !== 401 ||
        isAuthExcluded(request.url) ||
        request.url.includes('/auth/refresh-token')
      ) {
        return throwError(() => error);
      }

      return facadeService.refreshAccessToken().pipe(
        switchMap((newToken) => {
          if (!newToken) {
            facadeService.clearSession();
            void router.navigate(['/login']);
            return throwError(() => error);
          }
          const retry = request.clone({
            setHeaders: { Authorization: `Bearer ${newToken}` },
          });
          return next(retry);
        }),
        catchError((refreshErr) => {
          facadeService.clearSession();
          void router.navigate(['/login']);
          return throwError(() => refreshErr);
        }),
      );
    }),
  );
};
