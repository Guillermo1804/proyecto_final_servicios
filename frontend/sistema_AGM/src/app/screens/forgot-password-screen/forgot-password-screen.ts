import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { FacadeService } from '../../services/facade.service';

@Component({
  selector: 'app-forgot-password-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './forgot-password-screen.html',
  styleUrl: './forgot-password-screen.scss',
})
export class ForgotPasswordScreen {
  email = '';
  loading = false;
  message = '';
  errorMessage = '';

  constructor(
    private facade: FacadeService,
    private router: Router,
  ) {}

  submit(): void {
    this.errorMessage = '';
    this.message = '';
    if (!this.email.trim()) {
      this.errorMessage = 'Ingresa tu correo.';
      return;
    }
    this.loading = true;
    this.facade.forgotPassword(this.email.trim()).subscribe({
      next: () => {
        this.loading = false;
        this.message =
          'Si el correo está registrado, recibirás instrucciones para restablecer tu contraseña.';
      },
      error: () => {
        this.loading = false;
        this.message =
          'Si el correo está registrado, recibirás instrucciones para restablecer tu contraseña.';
      },
    });
  }
}
