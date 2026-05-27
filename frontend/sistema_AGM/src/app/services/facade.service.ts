import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { AgmApiResponse, LoginData } from '../models/auth-api.model';
import { AuthService } from './auth.service';
import { ValidatorService } from './tools/validator.service';
import { ErrorsService } from './tools/errors.service';

/**
 * Fachada legacy: delega autenticacion en AuthService (MS-1).
 * Otros modulos pueden seguir inyectando FacadeService hasta integrar cada MS.
 */
@Injectable({ providedIn: 'root' })
export class FacadeService {
  constructor(
    private auth: AuthService,
    private validatorService: ValidatorService,
    private errorService: ErrorsService,
  ) {}

  public validarLogin(username: string, password: string): Record<string, string> {
    const error: Record<string, string> = {};
    if (!this.validatorService.required(username)) {
      error['username'] = this.errorService.required;
    } else if (!this.validatorService.email(username)) {
      error['username'] = this.errorService.email;
    }
    if (!this.validatorService.required(password)) {
      error['password'] = this.errorService.required;
    }
    return error;
  }

  public login(
    username: string,
    password: string,
  ): Observable<AgmApiResponse<LoginData>> {
    return this.auth.login(username, password);
  }

  public storeTokens(response: AgmApiResponse<LoginData>, remember = false): string | null {
    if (!response?.data) {
      return null;
    }
    return this.auth.storeSession(response.data, remember) ? response.data.access_token : null;
  }

  public getAccessToken(): string | null {
    return this.auth.getAccessToken();
  }

  public getRefreshToken(): string | null {
    return this.auth.getRefreshToken();
  }

  public clearSession(): void {
    this.auth.clearSession();
  }

  public isAuthenticated(): boolean {
    return this.auth.isAuthenticated();
  }

  public getUserRole(): string | null {
    return this.auth.getUserRole();
  }

  public resolveHomeRoute(role: string | null): string {
    return this.auth.resolveHomeRoute(role);
  }

  public refreshToken(): Observable<string | null> {
    return this.auth.refreshTokenAndStore();
  }

  public logout(): void {
    this.auth.logout();
  }
}
