// This file can be replaced during build by using the `fileReplacements` array.
// `ng build` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.

export const environment = {
  production: false,
  /**
   * En desarrollo apuntamos directo al gateway para no depender del proxy de
   * `ng serve` ni de que el front se abra bajo el host correcto.
   */
  apiBaseUrl: 'http://127.0.0.1:8080',
  url_api: 'http://127.0.0.1:8080',
};
