import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'login-screen',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login-screen.html',
  styleUrls: ['./login-screen.scss']
})
export class LoginScreen {
  email = '';
  password = '';
  remember = false;
  showPassword = false;

  login() {
    // Aquí se integraría la lógica real de autenticación (llamada a servicio, gRPC, etc.)
    console.log('login', { email: this.email, password: this.password, remember: this.remember });
    // placeholder: navegar o mostrar feedback
  }


togglePassword(): void {
  this.showPassword = !this.showPassword;
}
}
