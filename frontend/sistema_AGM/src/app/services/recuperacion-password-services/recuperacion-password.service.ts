import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { AgmApiResponse } from '../../models/auth-api.model';
import { AuthService } from '../auth.service';

/** Recuperacion de contraseña — delega en MS-1 Auth. */
@Injectable({ providedIn: 'root' })
export class RecuperacionPasswordService {
  constructor(private auth: AuthService) {}

  sendResetLink(email: string): Observable<AgmApiResponse<null>> {
    return this.auth.forgotPassword(email);
  }

  resetPassword(token: string, password: string): Observable<AgmApiResponse<null>> {
    return this.auth.resetPassword(token, password);
  }
}
