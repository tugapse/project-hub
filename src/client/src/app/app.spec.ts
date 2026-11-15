import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { AppComponent } from './app';

describe('AppComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows the login screen when not authenticated', () => {
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    TestBed.inject(HttpTestingController)
      .expectOne('api/auth/me')
      .flush({ detail: 'Not authenticated' }, { status: 401, statusText: 'Unauthorized' });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('app-login')).not.toBeNull();
  });

  it('loads the projects once authenticated', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const backend = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    backend.expectOne('api/auth/me').flush({ username: 'admin', token_kind: 'session' });
    fixture.detectChanges();
    backend.expectOne('api/projects').flush([]);
    expect(fixture.nativeElement.querySelector('app-login')).toBeNull();
  });
});
