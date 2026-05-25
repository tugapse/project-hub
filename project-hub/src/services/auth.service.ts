import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private _isLoggedIn$ = new BehaviorSubject<boolean>(false);
  isLoggedIn$ = this._isLoggedIn$.asObservable();

  private get API_URL() {
    const host = window.location.hostname;
    const port = window.location.port;

    if (host === 'localhost' && port === '4200') {
      return 'http://localhost:9998/auth/token';
    }
    
    // Adjust for production environment if necessary
    const pathname = '/auth/token';
    return `http://${host}${port ? ':' + port : ''}${pathname}`;
  }

  constructor(private http: HttpClient) {
    const token = this.getToken();
    if (token) {
      // Here you might want to add a token validation request to the server
      this._isLoggedIn$.next(true);
    }
  }

  private getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  login(credentials: any): Observable<any> {
    const body = new URLSearchParams();
    body.set('username', credentials.username);
    body.set('password', credentials.password);

    return this.http.post(this.API_URL, body.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).pipe(
      tap((response: any) => {
        if (response.access_token) {
          localStorage.setItem('access_token', response.access_token);
          this._isLoggedIn$.next(true);
        }
      })
    );
  }

  logout(): void {
    localStorage.removeItem('access_token');
    this._isLoggedIn$.next(false);
  }
}