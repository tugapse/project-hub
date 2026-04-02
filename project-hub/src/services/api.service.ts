
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly API_URL = 'http://localhost:8000/projects';

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
        tasks: column.tasks.map(task => ({ ...task, checklist: task.checklist || [] }))
      }))
    }));
  }

}
