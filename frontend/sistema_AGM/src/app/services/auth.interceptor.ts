import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';

import { AuthService } from './auth.service';

const AUTH_EXCLUDED_PATTERNS = [
  '/auth/login',
  '/auth/logout',
  '/auth/refresh-token',
  '/auth/forgot-password',
  '/auth/reset-password',
];

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (AUTH_EXCLUDED_PATTERNS.some((pattern) => request.url.includes(pattern))) {
    return next(request);
  }

  const token = auth.getAccessToken();
  const authReq = token
    ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : request;

  return next(authReq).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status !== 401) {
        return throwError(() => err);
      }

      return auth.refreshTokenAndStore().pipe(
        switchMap((newAccess) => {
          if (!newAccess) {
            auth.clearSession();
            router.navigate(['/login']);
            return throwError(() => err);
          }
          const retried = request.clone({
            setHeaders: { Authorization: `Bearer ${newAccess}` },
          });
          return next(retried);
        }),
        catchError(() => {
          auth.clearSession();
          router.navigate(['/login']);
          return throwError(() => err);
        }),
      );
    }),
  );
};
