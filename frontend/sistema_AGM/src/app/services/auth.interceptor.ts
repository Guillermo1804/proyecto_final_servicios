import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { FacadeService } from './facade.service';
import { catchError, switchMap } from 'rxjs/operators';
import { throwError } from 'rxjs';
import { Router } from '@angular/router';

const AUTH_EXCLUDED_PATTERNS = ['/auth/login', '/auth/logout', '/auth/refresh', '/token'];

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const facadeService = inject(FacadeService);
  const router = inject(Router);

  if (AUTH_EXCLUDED_PATTERNS.some((pattern) => request.url.includes(pattern))) {
    return next(request);
  }

  const token = facadeService.getAccessToken();

  const authReq = token
    ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : request;

  return next(authReq).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status === 401) {
        return facadeService.refreshToken().pipe(
          switchMap((resp: any) => {
            const newToken = facadeService.getAccessToken();
            const retried = newToken
              ? request.clone({ setHeaders: { Authorization: `Bearer ${newToken}` } })
              : request;
            return next(retried);
          }),
          catchError(() => {
            facadeService.clearSession();
            try { router.navigate(['/login']); } catch {}
            return throwError(() => err);
          })
        );
      }

      return throwError(() => err);
    })
  );
};