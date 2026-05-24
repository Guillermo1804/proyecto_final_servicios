import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { RecuperacionPasswordService } from '../../services/recuperacion-password-services/recuperacion-password.service';

@Component({
  selector: 'app-reset-password-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './reset-password-screen.html',
  styleUrls: ['./reset-password-screen.scss']
})
export class ResetPasswordScreen {
  password = '';
  confirmPassword = '';
  loading = false;
  message = '';
  token = '';
  constructor(private recoveryService: RecuperacionPasswordService, private route: ActivatedRoute) {
    this.token = this.route.snapshot.queryParamMap.get('token') || '';
  }

  resetPassword(): void {
    this.message = '';

    if (!this.password || !this.confirmPassword) {
      this.message = 'Completa ambos campos';
      return;
    }

    if (this.password !== this.confirmPassword) {
      this.message = 'Las contraseñas no coinciden';
      return;
    }

    if (!this.token) {
      this.message = 'Token de restablecimiento no encontrado';
      return;
    }

    this.loading = true;

    this.recoveryService.resetPassword(this.token, this.password).subscribe(
      () => {
        this.loading = false;
        this.message = 'Tu contraseña se actualizó correctamente.';
      },
      (err) => {
        this.loading = false;
        this.message = err?.error?.message || 'Error al restablecer la contraseña';
      }
    );
  }
}