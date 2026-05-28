import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { AlumnosService } from './alumnos.service';

const STORAGE_PREFIX = 'agm_foto_perfil_v1_';
const MAX_BYTES = 1_500_000;

@Injectable({ providedIn: 'root' })
export class FotoPerfilService {
  /** Clave estable: alumno id, usuario id o correo. */
  buildUserKey(parts: { alumnoId?: number | null; usuarioId?: number | null; email?: string }): string {
    if (parts.alumnoId) {
      return `alumno-${parts.alumnoId}`;
    }
    if (parts.usuarioId) {
      return `usuario-${parts.usuarioId}`;
    }
    const email = (parts.email || '').trim().toLowerCase();
    return email ? `email-${email}` : 'anon';
  }

  getFotoDataUrl(userKey: string): string | null {
    if (!userKey || userKey === 'anon') {
      return null;
    }
    return localStorage.getItem(STORAGE_PREFIX + userKey);
  }

  guardarDesdeArchivo(userKey: string, file: File): Observable<string> {
    return new Observable((observer) => {
      if (!userKey || userKey === 'anon') {
        observer.error(new Error('No se pudo identificar tu cuenta para guardar la foto.'));
        return;
      }
      if (!file.type.startsWith('image/')) {
        observer.error(new Error('Selecciona un archivo de imagen (JPG, PNG o WebP).'));
        return;
      }
      if (file.size > MAX_BYTES) {
        observer.error(new Error('La imagen es muy pesada. Usa una menor a 1.5 MB.'));
        return;
      }

      const reader = new FileReader();
      reader.onload = () => {
        const dataUrl = String(reader.result || '');
        if (!dataUrl.startsWith('data:image/')) {
          observer.error(new Error('No se pudo leer la imagen.'));
          return;
        }
        localStorage.setItem(STORAGE_PREFIX + userKey, dataUrl);
        observer.next(dataUrl);
        observer.complete();
      };
      reader.onerror = () => observer.error(new Error('Error al leer el archivo.'));
      reader.readAsDataURL(file);
    });
  }

  eliminarFoto(userKey: string): void {
    if (userKey && userKey !== 'anon') {
      localStorage.removeItem(STORAGE_PREFIX + userKey);
    }
  }

  iniciales(nombre: string): string {
    return AlumnosService.inicialesDesdeNombre(nombre);
  }
}
