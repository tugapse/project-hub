
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map } from 'rxjs';
import { Project, Task } from '../entities/interfaces';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  
  // Relative to the document <base href>, so it works at "/" and behind a sub-path like "/hub/".
  // In dev, `ng serve` proxies /api to the Python server (see proxy.conf.json).
  private readonly API_URL = 'api/projects';

  constructor(private http: HttpClient) { }

  public fetchData() {
    return this.http.get<Project[]>(this.API_URL).pipe(map(this.mapProjects.bind(this)));
  }

  public save(projects: Project[]) {
    return this.http.post(this.API_URL, projects);
  }

  private mapProjects(data: Project[]) {
    return data.map((project: Project) => ({
      ...project,
      columns: project.columns.map(column => ({
        ...column,
        tasks: column.tasks.map(this.buildTask)
      }))
    }));
  }

  private buildTask(task:Task){
    return { ...task, checklistTitle: task.checklistTitle || 'Todo :', checklist: task.checklist || [] }
  }

}
