import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { FacadeService } from '../../services/facade.service';

@Component({
  selector: 'app-topbar-admin',
  imports: [],
  templateUrl: './topbar-admin.html',
  styleUrl: './topbar-admin.scss',
})
export class TopbarAdmin {
  constructor(
    private facadeService: FacadeService,
    private router: Router
  ) {}

  logout(): void {
    this.facadeService.logout().subscribe({
      next: () => this.router.navigate(['/login'], { replaceUrl: true }),
      error: () => {
        this.facadeService.clearSession();
        this.router.navigate(['/login'], { replaceUrl: true });
      },
    });
  }

}
