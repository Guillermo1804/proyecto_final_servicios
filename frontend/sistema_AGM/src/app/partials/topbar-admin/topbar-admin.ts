import { AsyncPipe, NgIf } from '@angular/common';
import { Component, inject } from '@angular/core';
import { map } from 'rxjs/operators';

import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-topbar-admin',
  imports: [AsyncPipe, NgIf],
  templateUrl: './topbar-admin.html',
  styleUrl: './topbar-admin.scss',
})
export class TopbarAdmin {
  private readonly auth = inject(AuthService);

  readonly session$ = this.auth.currentUser$.pipe(
    map((user) => {
      const role = this.auth.getUserRole();
      return {
        nombre: user?.nombre?.trim() || this.auth.getGreetingName(),
        email: user?.email?.trim() || '',
        rol: this.auth.getRoleLabel(role),
      };
    }),
  );

  logout(): void {
    this.auth.logout();
  }
}
