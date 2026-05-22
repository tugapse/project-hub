
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map } from 'rxjs';
import { Project, Task } from '../entities/interfaces';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  
  private get API_URL(){
    const host = window.location.hostname;
    const port = window.location.port;
    if(host === 'localhost' && port === '4200'){
      return 'http://localhost:9998/projects';
    } 

    return `http://${host}${ port ? ':' + port : '' }/projects`;
  } 

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
    console.log(task);
    return { ...task, checklistTitle: task.checklistTitle || 'Todo :', checklist: task.checklist || [] }
  }

}
