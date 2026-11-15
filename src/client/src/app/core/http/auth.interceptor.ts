import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';

import { AUTH_URL, AuthService } from '../services/auth.service';

/** Any 401 (other than a failed login attempt) means the session is gone: show the login screen. */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  return next(req).pipe(
    catchError((err: unknown) => {
      if (err instanceof HttpErrorResponse && err.status === 401 && !req.url.endsWith(`${AUTH_URL}/login`)) {
        auth.markAnonymous();
      }
      return throwError(() => err);
    }),
  );
};
