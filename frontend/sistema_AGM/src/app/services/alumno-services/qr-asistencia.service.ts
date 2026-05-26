import { Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import * as QRCode from 'qrcode';

import { AsistenciasService } from '../asistencias.service';

export interface QrAsistenciaSnapshot {
  materiaId: number;
  alumnoId: number;
  sesionId: number;
  encodedPayload: string;
  expiresIn: number;
  issuedAt: string;
  expiresAt: string;
  qrDataUrl: string;
}

@Injectable({
  providedIn: 'root',
})
export class QrAsistenciaService {
  constructor(private readonly asistencias: AsistenciasService) {}

  async generarQrDesdeBackend(materiaId: number, alumnoId: number): Promise<QrAsistenciaSnapshot> {
    const issuedAt = new Date();
    const token = await firstValueFrom(this.asistencias.generarQrToken(materiaId, alumnoId));

    const qrDataUrl = await QRCode.toDataURL(token.encoded_payload, {
      width: 260,
      margin: 1,
      errorCorrectionLevel: 'M',
    });

    const ttl = token.expires_in > 0 ? token.expires_in : 30;

    return {
      materiaId,
      alumnoId,
      sesionId: token.sesion_id,
      encodedPayload: token.encoded_payload,
      expiresIn: ttl,
      issuedAt: issuedAt.toISOString(),
      expiresAt: new Date(issuedAt.getTime() + ttl * 1000).toISOString(),
      qrDataUrl,
    };
  }
}
