// Reemplaza environment.ts en builds de produccion (ver angular.json fileReplacements si se activa).

export const environment = {
  production: true,
  /** Mismo host que el gateway (Nginx sirve API y front juntos) */
  apiBaseUrl: '',
  url_api: '',
};
