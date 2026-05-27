import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, finalize, shareReplay, switchMap, throwError } from 'rxjs';

import { AuthService } from './auth.service';

const AUTH_EXCLUDED_PATTERNS = [
  '/auth/login',
  '/auth/logout',
  '/auth/refresh-token',
  '/auth/forgot-password',
  '/auth/reset-password',
];

const AUTH_RETRY_HEADER = 'X-Auth-Retry';

let refreshInFlight: ReturnType<AuthService['refreshTokenAndStore']> | null = null;

function refreshOnce(auth: AuthService) {
  if (!refreshInFlight) {
    refreshInFlight = auth.refreshTokenAndStore().pipe(
      finalize(() => {
        refreshInFlight = null;
      }),
      shareReplay(1),
    );
  }
  return refreshInFlight;
}

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

      if (request.headers.has(AUTH_RETRY_HEADER)) {
        return throwError(() => err);
      }

      if (request.url.includes('/auth/refresh-token')) {
        auth.clearSession();
        router.navigate(['/login']);
        return throwError(() => err);
      }

      return refreshOnce(auth).pipe(
        switchMap((newAccess) => {
          if (!newAccess) {
            auth.clearSession();
            router.navigate(['/login']);
            return throwError(() => err);
          }
          const retried = request.clone({
            setHeaders: {
              Authorization: `Bearer ${newAccess}`,
              [AUTH_RETRY_HEADER]: '1',
            },
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
