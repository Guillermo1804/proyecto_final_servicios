import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-drop-confirm-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './drop-confirm-modal.html',
  styleUrls: ['./drop-confirm-modal.scss']
})
export class DropConfirmModal {
  @Input() visible = false;
  @Input() confirmationText = '';
  @Output() confirmationTextChange = new EventEmitter<string>();
  @Input() error: string | null = null;
  @Input() success: string | null = null;
  @Output() cancel = new EventEmitter<void>();
  @Output() confirm = new EventEmitter<void>();

  onInput(value: string) {
    this.confirmationTextChange.emit(value);
  }

  onCancel() { this.cancel.emit(); }
  onConfirm() { this.confirm.emit(); }
}
