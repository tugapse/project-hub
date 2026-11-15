import { Component, EventEmitter, Input, OnInit, Output, inject, signal } from '@angular/core';

import { AuthService, DeviceInfo, errorMessage } from '../../core/services/auth.service';

type ViewState = 'loading' | 'pending' | 'approved' | 'denied' | 'error';

/** Lets the logged-in user approve a device-flow request opened from a script/CLI. */
@Component({
  selector: 'app-device-approve',
  standalone: true,
  templateUrl: './device-approve.component.html',
  styleUrls: ['../../shared/auth-card.css'],
})
export class DeviceApproveComponent implements OnInit {
  private auth = inject(AuthService);

  @Input({ required: true }) userCode!: string;
  /** The user is done with this screen and wants to go to the app. */
  @Output() done = new EventEmitter<void>();

  readonly state = signal<ViewState>('loading');
  readonly device = signal<DeviceInfo | null>(null);
  readonly error = signal<string | null>(null);
  readonly busy = signal(false);

  ngOnInit() {
    this.auth.getDevice(this.userCode).subscribe({
      next: (info) => {
        this.device.set(info);
        this.state.set('pending');
      },
      error: (err) => this.fail(err, 'This code is invalid or has expired.'),
    });
  }

  decide(approve: boolean) {
    this.busy.set(true);
    this.auth.decideDevice(this.userCode, approve).subscribe({
      next: () => {
        this.busy.set(false);
        this.state.set(approve ? 'approved' : 'denied');
      },
      error: (err) => {
        this.busy.set(false);
        this.fail(err, 'This code is invalid or has expired.');
      },
    });
  }

  private fail(err: unknown, fallback: string) {
    this.error.set(errorMessage(err, fallback));
    this.state.set('error');
  }
}
