import { HttpErrorResponse } from '@angular/common/http';

import { environment } from '../../../environments/environment';
import { AgmApiResponse } from '../../models/auth-api.model';

export interface AgmPaginationMeta {
  page: number;
  total: number;
  limit: number;
}

export interface AgmListPage<T> {
  results: T[];
  count: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export function resolveApiBaseUrl(): string {
  const rawBase = environment.apiBaseUrl || environment.url_api || '';
  const baseUrl = rawBase.trim().replace(/\/$/, '');
  if (!baseUrl) {
    return '';
  }

  try {
    const parsed = new URL(baseUrl);
    const host = parsed.hostname.toLowerCase();
    if ((host === 'localhost' || host === '127.0.0.1') && !parsed.port) {
      return '';
    }
  } catch {
    // Keep non-URL values as-is.
  }

  return baseUrl;
}

export function buildApiUrl(path: string): string {
  const baseUrl = resolveApiBaseUrl();
  const normalizedPath = path.replace(/^\//, '');
  return baseUrl ? `${baseUrl}/${normalizedPath}` : `/${normalizedPath}`;
}

export function isAgmEnvelope(value: unknown): value is AgmApiResponse<unknown> {
  return Boolean(value && typeof value === 'object' && 'success' in (value as object));
}

export function unwrapAgmData<T>(response: unknown): T | null {
  if (isAgmEnvelope(response)) {
    return (response.data as T) ?? null;
  }
  return (response as T) ?? null;
}

export function extractAgmPagination(response: unknown): AgmPaginationMeta | null {
  if (!response || typeof response !== 'object') {
    return null;
  }
  const pagination = (response as { pagination?: AgmPaginationMeta }).pagination;
  if (!pagination) {
    return null;
  }
  return {
    page: Number(pagination.page) || 1,
    total: Number(pagination.total) || 0,
    limit: Number(pagination.limit) || 10,
  };
}

export function extractAgmListData<T>(response: unknown): T[] {
  const data = unwrapAgmData<unknown>(response);
  if (Array.isArray(data)) {
    return data as T[];
  }
  if (data && typeof data === 'object' && Array.isArray((data as { results?: T[] }).results)) {
    return (data as { results: T[] }).results;
  }
  if (Array.isArray(response)) {
    return response as T[];
  }
  return [];
}

export function buildListPage<T>(
  items: T[],
  page: number,
  pageSize: number,
  total?: number,
): AgmListPage<T> {
  const count = total ?? items.length;
  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  return {
    results: items,
    count,
    page: Math.min(page, totalPages),
    pageSize,
    totalPages,
  };
}

export function extractApiErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof HttpErrorResponse) {
    const body = error.error;
    if (body && typeof body === 'object' && 'message' in body) {
      return String((body as { message: string }).message || fallback);
    }
    if (error.status === 0) {
      return 'No se pudo conectar con el servidor. Verifica que Nginx y ms-periodos esten activos.';
    }
  }
  return fallback;
}
