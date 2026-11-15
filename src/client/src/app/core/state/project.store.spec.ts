import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { Project, ProjectStatus, Task } from '../models';
import { ProjectStore } from './project.store';

function task(id: number): Task {
  return { id, content: `t${id}`, description: '', color: '', icon: '', checklistTitle: '', checklist: [], notes: '' };
}

describe('ProjectStore', () => {
  let store: ProjectStore;

  beforeEach(() => {
    localStorage.removeItem('last-project-id');
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    store = TestBed.inject(ProjectStore);
  });

  function addProject(): Project {
    store.add('Test');
    return store.currentProject()!;
  }

  it('creates new projects as not started', () => {
    expect(addProject().status).toBe(ProjectStatus.NOT_STARTED);
  });

  it('keeps a project not started while tasks are only in the first column', () => {
    const project = addProject();
    project.columns[0].tasks.push(task(1));
    store.boardChanged();
    expect(project.status).toBe(ProjectStatus.NOT_STARTED);
  });

  it('promotes a not started project to active when a task leaves the first column', () => {
    const project = addProject();
    project.columns[1].tasks.push(task(1));
    store.boardChanged();
    expect(project.status).toBe(ProjectStatus.ACTIVE);
  });

  it('does not auto-change archived projects', () => {
    const project = addProject();
    store.setStatus(project, ProjectStatus.ARCHIVED);
    project.columns[2].tasks.push(task(1));
    store.boardChanged();
    expect(project.status).toBe(ProjectStatus.ARCHIVED);
  });

  it('lets the user move a project back to not started manually', () => {
    const project = addProject();
    project.columns[1].tasks.push(task(1));
    store.boardChanged();
    store.setStatus(project, ProjectStatus.NOT_STARTED);
    expect(project.status).toBe(ProjectStatus.NOT_STARTED);
  });
});
