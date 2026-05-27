// This file can be replaced during build by using the `fileReplacements` array.
// `ng build` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.

export const environment = {
  production: false,
  /**
   * Vacio con `ng serve`: las peticiones van a localhost:4200 y proxy.conf.json
   * las reenvia a Nginx (http://127.0.0.1:8080).
   * Si corres el front sin proxy, usa: 'http://127.0.0.1:8080'
   */
  apiBaseUrl: '',
  url_api: '',
};
