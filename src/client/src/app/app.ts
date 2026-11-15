import { Component, OnInit, inject, signal } from '@angular/core';

import { Task } from './core/models';
import { ThemeService } from './core/services/theme.service';
import { ProjectStore } from './core/state/project.store';
import { MainViewComponent } from './features/main-view/main-view.component';
import { SidebarComponent } from './features/sidebar/sidebar.component';
import { TaskModalComponent } from './features/task-modal/task-modal.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [TaskModalComponent, SidebarComponent, MainViewComponent],
  templateUrl: './app.html',
  styleUrls: ['./app.css'],
})
export class AppComponent implements OnInit {
  readonly store = inject(ProjectStore);
  readonly theme = inject(ThemeService);

  readonly isSidebarCollapsed = signal(false);
  /** Copy of the task being edited in the modal; null when the modal is closed. */
  readonly editingTask = signal<Task | null>(null);

  ngOnInit() {
    this.theme.init();
    this.store.load();
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
