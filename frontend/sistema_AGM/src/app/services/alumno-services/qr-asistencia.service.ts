import { Injectable } from '@angular/core';
import * as QRCode from 'qrcode';

export interface QrAsistenciaPayload {
  matricula: string;
  sessionId: string;
  issuedAt: string;
  kind: 'asistencia-qr';
}

export interface QrAsistenciaSnapshot {
  matricula: string;
  sessionId: string;
  issuedAt: string;
  expiresAt: string;
  qrDataUrl: string;
  token: string;
}

@Injectable({
  providedIn: 'root'
})
export class QrAsistenciaService {

  private readonly refreshSeconds = 5;
  private sessionKeyPromise: Promise<CryptoKey> | null = null;

  getRefreshSeconds(): number {
    return this.refreshSeconds;
  }

  async generarQrPersonal(matricula: string): Promise<QrAsistenciaSnapshot> {
    const issuedAt = new Date();
    const sessionId = this.generarSessionId();
    const payload: QrAsistenciaPayload = {
      matricula,
      sessionId,
      issuedAt: issuedAt.toISOString(),
      kind: 'asistencia-qr'
    };

    const token = await this.cifrarPayload(payload);
    const qrDataUrl = await QRCode.toDataURL(token, {
      width: 260,
      margin: 1,
      errorCorrectionLevel: 'M'
    });

    return {
      matricula,
      sessionId,
      issuedAt: payload.issuedAt,
      expiresAt: new Date(issuedAt.getTime() + this.refreshSeconds * 1000).toISOString(),
      qrDataUrl,
      token
    };
  }

  private generarSessionId(): string {
    if (typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID();
    }

    return `ses-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  }

  private async cifrarPayload(payload: QrAsistenciaPayload): Promise<string> {
    const key = await this.getSessionKey();
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encoded = new TextEncoder().encode(JSON.stringify(payload));
    const encrypted = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      key,
      encoded
    );

    return `AGMQR.${this.toBase64(iv)}.${this.toBase64(new Uint8Array(encrypted))}`;
  }

  private async getSessionKey(): Promise<CryptoKey> {
    if (!this.sessionKeyPromise) {
      const keyBytes = crypto.getRandomValues(new Uint8Array(32));
      this.sessionKeyPromise = crypto.subtle.importKey(
        'raw',
        keyBytes,
        'AES-GCM',
        false,
        ['encrypt']
      );
    }

    return this.sessionKeyPromise;
  }

  private toBase64(bytes: Uint8Array): string {
    let binary = '';

    bytes.forEach((byte) => {
      binary += String.fromCharCode(byte);
    });

    return btoa(binary);
  }
}
