import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { PROJECT_STATUS_LABELS, ProjectStatus } from '../../core/models';

/** Small icon illustrating a project's status (active / not started / archived). */
@Component({
  selector: 'app-project-status-icon',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '[class]': '"status-icon " + status()',
    '[attr.title]': 'label()',
    role: 'img',
    '[attr.aria-label]': 'label()',
  },
  template: `
    <svg viewBox="0 0 16 16" aria-hidden="true">
      @switch (status()) {
        @case ('active') {
          <circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.5" />
          <path d="M6.5 5.2v5.6L11 8z" fill="currentColor" />
        }
        @case ('not_started') {
          <circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.5"
            stroke-dasharray="2.6 2.1" />
        }
        @case ('archived') {
          <rect x="1.75" y="2.5" width="12.5" height="3.5" rx="1" fill="none" stroke="currentColor"
            stroke-width="1.5" />
          <path d="M3 6v6.5a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V6M6.5 8.75h3" fill="none"
            stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
        }
      }
    </svg>
  `,
  styles: `
    :host {
      display: inline-flex;
      width: var(--status-icon-size, 14px);
      height: var(--status-icon-size, 14px);
      flex-shrink: 0;
    }
    svg { width: 100%; height: 100%; }
    :host(.active) { color: var(--neon-green); }
    :host(.not_started) { color: var(--text-muted); }
    :host(.archived) { color: var(--text-muted); opacity: 0.8; }
  `,
})
export class ProjectStatusIconComponent {
  readonly status = input.required<ProjectStatus>();
  readonly label = computed(() => PROJECT_STATUS_LABELS[this.status()]);
}
