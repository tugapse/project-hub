import { CdkDragDrop, moveItemInArray, DragDropModule } from "@angular/cdk/drag-drop";
import { CommonModule } from "@angular/common";
import { Component, EventEmitter, Input, Output, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { TASK_COLORS, TASK_ICONS, Task, ChecklistItem } from '../../core/models';
import { ConfirmService } from '../../core/services/confirm.service';

@Component({
  selector: 'task-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, DragDropModule],
  templateUrl: './task-modal.component.html',
  styleUrls: ['./task-modal.component.css'],
})
export class TaskModalComponent {
  private readonly confirm = inject(ConfirmService);

  drop(event: CdkDragDrop<ChecklistItem[]>) {
    if (this.editingTask && this.editingTask.checklist) {
      moveItemInArray(this.editingTask.checklist, event.previousIndex, event.currentIndex);
    }
  }

  public readonly TASK_COLORS = TASK_COLORS;
  public readonly TASK_ICONS = TASK_ICONS;

  @Input() editingTask: Task | null = null;
  @Input() showPopup: boolean = false;

  @Output() update = new EventEmitter<Task>();
  @Output() close = new EventEmitter<void>();

  addChecklistItem(text: string) {
    if (text && this.editingTask) {
      if (!this.editingTask.checklist) {
        this.editingTask.checklist = [];
      }
      this.editingTask.checklist.push({ text, completed: false });
    }
  }

  async deleteChecklistItem(item: ChecklistItem) {
    const checklist = this.editingTask?.checklist;
    if (!checklist) return;
    const confirmed = await this.confirm.confirm({
      title: 'Delete item',
      message: item.text
        ? `Are you sure you want to delete "${item.text}"?`
        : 'Are you sure you want to delete this item?',
    });
    // Look the item up again: the list may have been reordered while the dialog was open.
    const index = checklist.indexOf(item);
    if (confirmed && index !== -1) {
      checklist.splice(index, 1);
    }
  }

  getChecklistProgress(task: Task): { completed: number, percentage: number } {
    if (!task.checklist || task.checklist.length === 0) {
      return { completed: 0, percentage: 0 };
    }
    const completed = task.checklist.filter((item: ChecklistItem) => item.completed).length;
    const percentage = (completed / task.checklist.length) * 100;
    return { completed, percentage };
  }

  saveAndClose() {
    if (!this.editingTask) return;
    this.update.emit(this.editingTask);
  }

  cancel() {
    this.close.emit();
  }

  updateTask(key: 'color' | 'icon', value: string) {
    if (!this.editingTask) return;
    if (key === 'color') this.editingTask.color = value;
    if (key === 'icon') this.editingTask.icon = value;
  }
}