// This file can be replaced during build by using the `fileReplacements` array.
// `ng build` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.

export const environment = {
  production: false,
  /** Gateway Nginx (recomendado): MS-1 en /auth/* */
  apiBaseUrl: 'http://127.0.0.1:8080',
  /** Alias legacy usado por algunos servicios */
  url_api: 'http://127.0.0.1:8080',
  /** Solo MS-1 directo (sin Nginx): http://127.0.0.1:8001 */
};
