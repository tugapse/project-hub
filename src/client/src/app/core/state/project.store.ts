import { DestroyRef, Injectable, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subject, catchError, concatMap, debounceTime, map, of } from 'rxjs';

import { Column, Project, ProjectStatus, SyncState, Task } from '../models';
import { ApiService } from '../services/api.service';
import { AuthService } from '../services/auth.service';

/** Prefix of the localStorage key that remembers each user's last opened project. */
const LAST_PROJECT_KEY = 'last-project-id';
const SAVE_DEBOUNCE_MS = 300;

/**
 * Single source of truth for projects and their sync state.
 *
 * Components still mutate project objects in place (drag & drop, inline edits)
 * and then call `save()`. Saves are debounced and sent one at a time, in order,
 * so rapid changes never race each other on the server.
 */
@Injectable({ providedIn: 'root' })
export class ProjectStore {
  private api = inject(ApiService);
  private auth = inject(AuthService);

  readonly projects = signal<Project[]>([]);
  readonly currentProject = signal<Project | null>(null);
  readonly syncState = signal<SyncState>('synced');

  private saveRequests = new Subject<number>();
  private saveVersion = 0;

  constructor() {
    this.saveRequests
      .pipe(
        debounceTime(SAVE_DEBOUNCE_MS),
        concatMap((version) =>
          this.api.saveProjects(this.projects()).pipe(
            map(() => ({ version, ok: true })),
            catchError(() => of({ version, ok: false })),
          ),
        ),
        takeUntilDestroyed(inject(DestroyRef)),
      )
      .subscribe(({ version, ok }) => {
        if (!ok) {
          this.syncState.set('error');
        } else if (version === this.saveVersion) {
          this.syncState.set('synced');
        }
      });
  }

  private get lastProjectKey(): string {
    return `${LAST_PROJECT_KEY}:${this.auth.username() ?? ''}`;
  }

  load() {
    // Drop whatever a previously signed-in user had open.
    this.projects.set([]);
    this.currentProject.set(null);
    this.api.fetchProjects().subscribe((projects) => {
      this.projects.set(projects);
      const lastId = localStorage.getItem(this.lastProjectKey);
      if (lastId) {
        const project = projects.find((p) => p.id === lastId) ?? projects[0] ?? null;
        if (project && project.status !== ProjectStatus.ARCHIVED) {
          this.select(project);
        }
      }
    });
  }

  save() {
    this.syncState.set('syncing');
    this.saveRequests.next(++this.saveVersion);
  }

  // --- Projects ---

  select(project: Project) {
    this.currentProject.set(project);
    if (project.status !== ProjectStatus.ARCHIVED) {
      localStorage.setItem(this.lastProjectKey, project.id);
    }
  }

  add(name: string) {
    name = name.trim();
    if (!name) return;
    const project: Project = {
      id: Date.now().toString(),
      name,
      columns: [
        { id: 'todo', title: 'To Do', tasks: [] },
        { id: 'doing', title: 'Doing', tasks: [] },
        { id: 'done', title: 'Done', tasks: [] },
      ],
      status: ProjectStatus.NOT_STARTED,
    };
    this.projects.update((list) => [...list, project]);
    this.select(project);
    this.save();
  }

  setStatus(project: Project, status: ProjectStatus) {
    if (project.status === status) return;
    project.status = status;
    this.projects.update((list) => [...list]);
    this.save();
  }

  /**
   * Call after tasks are added or moved on the board. A not-started project
   * becomes active as soon as any task leaves the first column.
   */
  boardChanged() {
    const project = this.currentProject();
    if (project?.status === ProjectStatus.NOT_STARTED && hasStarted(project)) {
      project.status = ProjectStatus.ACTIVE;
      this.projects.update((list) => [...list]);
    }
    this.save();
  }

  delete(project: Project) {
    const remaining = this.projects().filter((p) => p.id !== project.id);
    this.projects.set(remaining);
    if (this.currentProject()?.id === project.id) {
      this.currentProject.set(remaining[0] ?? null);
    }
    this.save();
  }

  // --- Tasks ---

  updateTask(updated: Task) {
    const project = this.currentProject();
    if (!project) return;
    for (const column of project.columns) {
      const index = column.tasks.findIndex((t) => t.id === updated.id);
      if (index !== -1) {
        column.tasks[index] = updated;
        break;
      }
    }
    this.save();
  }

  deleteTask(column: Column, task: Task) {
    const index = column.tasks.findIndex((t) => t.id === task.id);
    if (index !== -1) {
      column.tasks.splice(index, 1);
      this.save();
    }
  }
}

function hasStarted(project: Project): boolean {
  return project.columns.slice(1).some((column) => column.tasks.length > 0);
}
