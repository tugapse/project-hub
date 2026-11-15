import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DragDropModule, CdkDropList, CdkDragDrop } from '@angular/cdk/drag-drop';
import { TaskCardComponent } from '../task-card/task-card.component';
import { Column, Task } from '../../../core/models';
import { ConfirmService } from '../../../core/services/confirm.service';

@Component({
  selector: 'app-column',
  standalone: true,
  imports: [CommonModule, DragDropModule, TaskCardComponent],
  templateUrl: './column.component.html',
  styleUrls: ['./column.component.css'],
})
export class ColumnComponent {
  private readonly confirm = inject(ConfirmService);

  @Input() column: Column | null = null;
  @Input() cdkDropListConnectedTo: CdkDropList[] = [];

  @Output() taskOpened = new EventEmitter<Task>();
  @Output() taskDeleted = new EventEmitter<{ column: Column; task: Task }>();
  @Output() stateChanged = new EventEmitter<void>();
  @Output() cdkDropListDropped = new EventEmitter<CdkDragDrop<Task[]>>();

  openTaskPopup(task: Task) {
    this.taskOpened.emit(task);
  }

  async deleteTask(task: Task) {
    const column = this.column;
    if (!column) return;
    const confirmed = await this.confirm.confirm({
      title: 'Delete task',
      message: `Are you sure you want to delete task "${task.content}"?`,
    });
    if (confirmed) {
      this.taskDeleted.emit({ column, task });
    }
  }

  addTask(inputElement: HTMLInputElement) {
    const content = inputElement.value;
    if (content.trim() && this.column) {
      this.column.tasks.push({
        id: Date.now(),
        content,
        description: '',
        color: '#475569',
        icon: '',
        checklistTitle: 'Todos :',
        checklist: [],
        notes: '',
      });
      inputElement.value = '';
      this.stateChanged.emit();
    }
  }
}