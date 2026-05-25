import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { RecuperacionPasswordService } from '../../services/recuperacion-password-services/recuperacion-password.service';


@Component({
  selector: 'app-forgot-password-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './forgot-password-screen.html',
  styleUrls: ['./forgot-password-screen.scss']
})
export class ForgotPasswordScreen {
  email = '';
  loading = false;
  message = '';
  constructor(private recoveryService: RecuperacionPasswordService) {}

  sendResetLink(): void {
    this.message = '';

    if (!this.email) {
      this.message = 'Ingresa tu correo institucional';
      return;
    }

    this.loading = true;

    this.recoveryService.sendResetLink(this.email).subscribe(
      () => {
        this.loading = false;
        this.message = 'Si el correo existe, recibirás un enlace para restablecer tu contraseña.';
      },
      (err) => {
        this.loading = false;
        this.message = err?.error?.message || 'Error al solicitar el enlace de recuperación';
      }
    );
  }
}