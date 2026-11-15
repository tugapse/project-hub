import { Component, OnInit, effect, inject, signal, untracked } from '@angular/core';

import { Task } from './core/models';
import { AuthService } from './core/services/auth.service';
import { ThemeService } from './core/services/theme.service';
import { ProjectStore } from './core/state/project.store';
import { DeviceApproveComponent } from './features/device-approve/device-approve.component';
import { LoginComponent } from './features/login/login.component';
import { MainViewComponent } from './features/main-view/main-view.component';
import { SidebarComponent } from './features/sidebar/sidebar.component';
import { TaskModalComponent } from './features/task-modal/task-modal.component';
import { ConfirmDialogComponent } from './shared/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    TaskModalComponent,
    SidebarComponent,
    MainViewComponent,
    LoginComponent,
    DeviceApproveComponent,
    ConfirmDialogComponent,
  ],
  templateUrl: './app.html',
  styleUrls: ['./app.css'],
})
export class AppComponent implements OnInit {
  readonly auth = inject(AuthService);
  readonly store = inject(ProjectStore);
  readonly theme = inject(ThemeService);

  /** Set when the page was opened from a device-flow link (`?user_code=XXXX-XXXX`). */
  readonly deviceUserCode = signal<string | null>(new URLSearchParams(location.search).get('user_code'));

  readonly isSidebarCollapsed = signal(false);
  /** Copy of the task being edited in the modal; null when the modal is closed. */
  readonly editingTask = signal<Task | null>(null);

  constructor() {
    // (Re)load the projects every time the user becomes authenticated.
    effect(() => {
      if (this.auth.status() === 'authenticated') {
        untracked(() => this.store.load());
      }
    });
  }

  ngOnInit() {
    this.theme.init();
    this.auth.check();
  }

  /** Leaves the device approval screen and drops the code from the URL. */
  closeDeviceApproval() {
    this.deviceUserCode.set(null);
    const url = new URL(location.href);
    url.searchParams.delete('user_code');
    history.replaceState(history.state, '', url);
  }

  openTask(task: Task) {
    this.editingTask.set({ ...task, checklist: task.checklist.map((i) => ({ ...i })) });
  }

  saveTask(task: Task) {
    this.store.updateTask(task);
    this.closeTask();
  }

  closeTask() {
    this.editingTask.set(null);
  }

  toggleSidebar() {
    this.isSidebarCollapsed.update((v) => !v);
  }
}
