import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FacadeService } from '../../services/facade.service';
import { Router, RouterLink } from '@angular/router';

@Component({
  selector: 'login-screen',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './login-screen.html',
  styleUrls: ['./login-screen.scss']
})
export class LoginScreen {
  email = '';
  password = '';
  remember = false;
  showPassword = false;
  loading = false;
  errorMessage = '';

  constructor(private facadeService: FacadeService, private router: Router) {}

  login(): void {
    this.errorMessage = '';
    
    if (!this.email || !this.password) {
      this.errorMessage = 'Por favor completa todos los campos';
      return;
    }

    this.loading = true;

    this.facadeService.login(this.email, this.password).subscribe(
      (response) => {
        console.log('Login response:', response);
        this.loading = false;
        
        if (response?.success || response?.data?.access_token) {
          // Guardar tokens
          this.facadeService.storeTokens(response, this.remember);
          
          // Obtener rol desde el JWT
          const role = this.facadeService.getUserRole();
          console.log('Role obtained:', role);
          
          // Redirigir según el rol
          const homeRoute = this.facadeService.resolveHomeRoute(role);
          console.log('Home route:', homeRoute);
          this.router.navigate([homeRoute]);
        } else {
          this.errorMessage = 'Error de autenticacion';
        }
      },
      (error) => {
        this.loading = false;
        if (error?.status === 401) {
          this.errorMessage = 'Credenciales invalidas';
        } else {
          this.errorMessage = error?.error?.message || 'Error en la autenticacion';
        }
      }
    );
  }

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }
}
