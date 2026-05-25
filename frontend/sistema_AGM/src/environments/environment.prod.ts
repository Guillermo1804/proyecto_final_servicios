import { buildMicroservicesConfig } from '../app/config/microservices.config';
import { AgmEnvironment } from './environment.types';

/** Produccion: front servido junto al gateway (mismo host) o apiBaseUrl del deploy */
export const environment: AgmEnvironment = {
  production: true,
  integrationMode: 'gateway',
  apiBaseUrl: '',
  url_api: '',
  microservices: buildMicroservicesConfig('direct', {
    ms1_auth: { enabled: true },
    ms2_periodos: { enabled: false },
    ms3_alumnos: { enabled: false },
    ms4_calificaciones: { enabled: false },
    ms5_asistencias: { enabled: false },
    ms6_notificaciones: { enabled: false },
    ms7_reportes: { enabled: false },
  }),
};
