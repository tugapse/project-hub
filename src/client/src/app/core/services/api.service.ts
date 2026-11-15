import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map } from 'rxjs';
import { Project, Task } from '../models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);

  // Relative to the document <base href>, so it works at "/" and behind a sub-path like "/hub/".
  // In dev, `ng serve` proxies /api to the Python server (see proxy.conf.json).
  private readonly API_URL = 'api/projects';

  fetchProjects() {
    return this.http
      .get<Project[]>(this.API_URL)
      .pipe(map((projects) => projects.map((p) => this.normalizeProject(p))));
  }

  saveProjects(projects: Project[]) {
    return this.http.post(this.API_URL, projects);
  }

  private normalizeProject(project: Project): Project {
    return {
      ...project,
      columns: project.columns.map((column) => ({
        ...column,
        tasks: column.tasks.map((task) => this.normalizeTask(task)),
      })),
    };
  }

  private normalizeTask(task: Task): Task {
    return {
      ...task,
      checklistTitle: task.checklistTitle || 'Todo :',
      checklist: task.checklist || [],
    };
  }
}
