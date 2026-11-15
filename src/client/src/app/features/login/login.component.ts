import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { AuthService, errorMessage } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['../../shared/auth-card.css'],
})
export class LoginComponent {
  private auth = inject(AuthService);

  username = '';
  password = '';
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);

  submit() {
    if (!this.username || !this.password || this.busy()) return;
    this.busy.set(true);
    this.error.set(null);
    this.auth.login(this.username, this.password).subscribe({
      next: () => this.busy.set(false),
      error: (err) => {
        this.busy.set(false);
        this.password = '';
        this.error.set(errorMessage(err, 'Login failed.'));
      },
    });
  }
}
