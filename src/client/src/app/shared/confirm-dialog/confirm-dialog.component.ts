import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  afterRenderEffect,
  inject,
  viewChild,
} from '@angular/core';
import { ConfirmService } from '../../core/services/confirm.service';

/** Modal rendered from the state of `ConfirmService`; mount it once in the app root. */
@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '(document:keydown.escape)': 'onEscape()',
  },
  template: `
    @if (confirm.pending(); as dialog) {
      <div class="confirm-overlay" (click)="confirm.close(false)">
        <div
          class="confirm-modal"
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="confirm-title"
          aria-describedby="confirm-message"
          (click)="$event.stopPropagation()"
        >
          <h3 id="confirm-title">{{ dialog.title }}</h3>
          <p id="confirm-message">{{ dialog.message }}</p>
          <div class="confirm-actions">
            <button type="button" class="btn-cancel" (click)="confirm.close(false)">
              {{ dialog.cancelText }}
            </button>
            <button
              #confirmBtn
              type="button"
              class="btn-confirm"
              [class.danger]="dialog.danger"
              (click)="confirm.close(true)"
            >
              {{ dialog.confirmText }}
            </button>
          </div>
        </div>
      </div>
    }
  `,
  styles: `
    .confirm-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.6);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1100; /* above the task modal */
    }
    .confirm-modal {
      background: var(--bg-card);
      color: var(--text-main);
      border: 1px solid var(--border);
      border-radius: 8px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
      width: 400px;
      max-width: calc(100vw - 32px);
      padding: 20px 24px;
      box-sizing: border-box;
    }
    h3 {
      margin: 0 0 8px;
      font-size: 1.1rem;
    }
    p {
      margin: 0 0 20px;
      color: var(--text-muted);
      line-height: 1.4;
      word-break: break-word;
    }
    .confirm-actions {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }
    button {
      padding: 8px 18px;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
    }
    .btn-cancel {
      background: transparent;
      color: var(--text-muted);
      border: 1px solid var(--border);
    }
    .btn-confirm {
      background: var(--neon-blue);
      color: #fff;
      border: none;
    }
    .btn-confirm.danger {
      background: var(--neon-red);
    }
  `,
})
export class ConfirmDialogComponent {
  readonly confirm = inject(ConfirmService);
  private readonly confirmBtn = viewChild<ElementRef<HTMLButtonElement>>('confirmBtn');

  constructor() {
    // Focus the confirm button when the dialog opens so Enter confirms.
    afterRenderEffect(() => this.confirmBtn()?.nativeElement.focus());
  }

  onEscape() {
    this.confirm.close(false);
  }
}
