import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FacadeService } from '../../services/facade.service';

@Component({
  selector: 'app-reset-password-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './reset-password-screen.html',
  styleUrl: './reset-password-screen.scss',
})
export class ResetPasswordScreen implements OnInit {
  token = '';
  password = '';
  confirm = '';
  loading = false;
  message = '';
  errorMessage = '';

  constructor(
    private route: ActivatedRoute,
    private facade: FacadeService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    this.token = this.route.snapshot.queryParamMap.get('token') ?? '';
  }

  submit(): void {
    this.errorMessage = '';
    this.message = '';
    if (!this.token) {
      this.errorMessage = 'Token inválido o ausente en el enlace.';
      return;
    }
    if (this.password.length < 8) {
      this.errorMessage = 'La contraseña debe tener al menos 8 caracteres.';
      return;
    }
    if (this.password !== this.confirm) {
      this.errorMessage = 'Las contraseñas no coinciden.';
      return;
    }
    this.loading = true;
    this.facade.resetPassword(this.token, this.password).subscribe({
      next: () => {
        this.loading = false;
        this.message = 'Contraseña actualizada. Redirigiendo al login…';
        setTimeout(() => this.router.navigate(['/login']), 2000);
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'Token inválido o expirado.';
      },
    });
  }
}
