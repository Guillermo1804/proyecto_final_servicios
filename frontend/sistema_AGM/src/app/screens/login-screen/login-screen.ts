import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../services/auth.service';
import { ValidatorService } from '../../services/tools/validator.service';
import { ErrorsService } from '../../services/tools/errors.service';

@Component({
  selector: 'login-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './login-screen.html',
  styleUrls: ['./login-screen.scss'],
})
export class LoginScreen {
  email = '';
  password = '';
  remember = false;
  showPassword = false;
  loading = false;
  errorMessage = '';

  constructor(
    private auth: AuthService,
    private router: Router,
    private validator: ValidatorService,
    private errors: ErrorsService,
  ) {}

  login(): void {
    this.errorMessage = '';
    const validation = this.validateForm();
    if (Object.keys(validation).length > 0) {
      this.errorMessage = 'Revisa el correo y la contraseña';
      return;
    }

    this.loading = true;
    this.auth.login(this.email.trim(), this.password).subscribe({
      next: (response) => {
        this.loading = false;
        if (!response?.success || !response.data?.access_token) {
          this.errorMessage = response?.message || 'Error de autenticacion';
          return;
        }

        this.auth.storeSession(response.data, this.remember);
        this.auth.refreshCurrentUser().subscribe({
          next: () => {
            const role = this.auth.getUserRole();
            this.router.navigate([this.auth.resolveHomeRoute(role)]);
          },
          error: () => {
            const role = this.auth.getUserRole();
            this.router.navigate([this.auth.resolveHomeRoute(role)]);
          },
        });
      },
      error: (error) => {
        this.loading = false;
        if (error?.status === 401) {
          this.errorMessage = 'Credenciales invalidas';
        } else if (error?.status === 0) {
          this.errorMessage =
            'No se pudo conectar con el servidor. Verifica que Nginx (:8080) y MS-1 esten activos.';
        } else {
          this.errorMessage = error?.error?.message || 'Error en la autenticacion';
        }
      },
    });
  }

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  private validateForm(): Record<string, string> {
    const errs: Record<string, string> = {};
    if (!this.validator.required(this.email)) {
      errs['email'] = this.errors.required;
    } else if (!this.validator.email(this.email)) {
      errs['email'] = this.errors.email;
    }
    if (!this.validator.required(this.password)) {
      errs['password'] = this.errors.required;
    }
    return errs;
  }
}
