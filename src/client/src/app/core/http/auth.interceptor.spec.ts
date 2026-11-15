import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { AuthService } from '../services/auth.service';
import { authInterceptor } from './auth.interceptor';

describe('authInterceptor', () => {
  let http: HttpClient;
  let backend: HttpTestingController;
  let auth: AuthService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(withInterceptors([authInterceptor])), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpClient);
    backend = TestBed.inject(HttpTestingController);
    auth = TestBed.inject(AuthService);
    auth.status.set('authenticated');
  });

  afterEach(() => backend.verify());

  it('marks the user as anonymous on a 401', () => {
    http.get('api/projects').subscribe({ error: () => {} });
    backend.expectOne('api/projects').flush({ detail: 'Not authenticated' }, { status: 401, statusText: 'Unauthorized' });
    expect(auth.status()).toBe('anonymous');
  });

  it('ignores a 401 from a failed login attempt', () => {
    auth.status.set('anonymous');
    http.post('api/auth/login', {}).subscribe({ error: () => {} });
    backend.expectOne('api/auth/login').flush({ detail: 'Invalid' }, { status: 401, statusText: 'Unauthorized' });
    expect(auth.status()).toBe('anonymous');
  });

  it('keeps the session on other errors', () => {
    http.get('api/projects').subscribe({ error: () => {} });
    backend.expectOne('api/projects').flush({}, { status: 500, statusText: 'Server Error' });
    expect(auth.status()).toBe('authenticated');
  });
});
