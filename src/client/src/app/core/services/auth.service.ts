import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, catchError, map, of, tap } from 'rxjs';

export type AuthStatus = 'unknown' | 'anonymous' | 'authenticated';

export interface DeviceInfo {
  user_code: string;
  client_name: string;
  expires_in: number;
}

interface MeResponse {
  username: string;
  token_kind: string;
}

/** URLs are relative to the document <base href> (see ApiService). */
export const AUTH_URL = 'api/auth';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);

  readonly status = signal<AuthStatus>('unknown');
  readonly username = signal<string | null>(null);

  /** Asks the server whether the session cookie is still valid. */
  check(): void {
    this.http
      .get<MeResponse>(`${AUTH_URL}/me`)
      .pipe(catchError(() => of(null)))
      .subscribe((me) => (me ? this.setAuthenticated(me.username) : this.markAnonymous()));
  }

  login(username: string, password: string): Observable<void> {
    return this.http
      .post<MeResponse>(`${AUTH_URL}/login`, { username, password })
      .pipe(
        tap((me) => this.setAuthenticated(me.username)),
        map(() => undefined),
      );
  }

  logout(): void {
    this.http
      .post(`${AUTH_URL}/logout`, {})
      .pipe(catchError(() => of(null)))
      .subscribe(() => this.markAnonymous());
  }

  getDevice(userCode: string): Observable<DeviceInfo> {
    return this.http.get<DeviceInfo>(`${AUTH_URL}/device/${encodeURIComponent(userCode)}`);
  }

  decideDevice(userCode: string, approve: boolean): Observable<void> {
    return this.http
      .post(`${AUTH_URL}/device/approve`, { user_code: userCode, approve })
      .pipe(map(() => undefined));
  }

  markAnonymous(): void {
    this.status.set('anonymous');
    this.username.set(null);
  }

  private setAuthenticated(username: string): void {
    this.username.set(username);
    this.status.set('authenticated');
  }
}

/** Extracts a readable message from a FastAPI error response. */
export function errorMessage(err: unknown, fallback: string): string {
  if (err instanceof HttpErrorResponse) {
    const detail = err.error?.detail;
    if (typeof detail === 'string') return detail;
    if (err.status === 0) return 'Server unreachable.';
  }
  return fallback;
}
