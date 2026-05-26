/** Días laborables en UI (LUN–VIE). */
export const DIAS_SEMANA_LAB = ['LUN', 'MAR', 'MIÉ', 'JUE', 'VIE'] as const;

/**
 * Códigos de día en horarios BUAP.
 * Martes se representa con la letra A (ej. "L 1000-1059 / A 0900-1059 / J 0900-1059").
 */
export const DIA_ALIASES: Record<string, string[]> = {
  LUN: ['LUN', 'L', 'LU', 'LUNES'],
  MAR: ['MAR', 'MA', 'A', 'MARTES'],
  'MIÉ': ['MIÉ', 'MIE', 'MI', 'X', 'MIERCOLES', 'MIÉRCOLES'],
  JUE: ['JUE', 'J', 'JU', 'JUEVES'],
  VIE: ['VIE', 'V', 'VI', 'VIERNES'],
  SÁB: ['SÁB', 'SAB', 'SA', 'SABADO', 'SÁBADO'],
  DOM: ['DOM', 'D', 'DO', 'DOMINGO'],
};

export function tokenizarHorario(horario: string): string[] {
  return horario
    .toUpperCase()
    .replace(/[\/\s,]+/g, ' ')
    .split(' ')
    .map((t) => t.trim())
    .filter(Boolean);
}

export function parseDiasDesdeHorario(
  horario: string,
  dias: readonly string[] = DIAS_SEMANA_LAB,
): string[] {
  if (!horario.trim()) {
    return [];
  }
  const tokens = tokenizarHorario(horario);
  const encontrados: string[] = [];
  for (const dia of dias) {
    const aliases = DIA_ALIASES[dia] ?? [];
    if (tokens.some((token) => aliases.includes(token))) {
      encontrados.push(dia);
    }
  }
  return encontrados;
}

export function horarioIncluyeDia(horario: string, dia: string): boolean {
  if (!horario.trim()) {
    return dia === 'LUN';
  }
  const aliases = DIA_ALIASES[dia] ?? [];
  return tokenizarHorario(horario).some((token) => aliases.includes(token));
}

/** Convierte franjas BUAP (ej. 0900-1059) a reloj legible (09:00-10:59). */
export function formatFranjaHorario(raw: string): string {
  const value = raw.trim();
  const buap = value.match(/^(\d{3,4})\s*-\s*(\d{3,4})$/);
  if (buap) {
    const toClock = (n: string) => {
      const padded = n.padStart(4, '0');
      return `${padded.slice(0, 2)}:${padded.slice(2, 4)}`;
    };
    return `${toClock(buap[1])}-${toClock(buap[2])}`;
  }

  const standard = value.match(/^(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})$/);
  if (standard) {
    return `${standard[1].padStart(2, '0')}:${standard[2]}-${standard[3].padStart(2, '0')}:${standard[4]}`;
  }

  const single = value.match(/\d{1,2}:\d{2}/);
  return single ? single[0] : value;
}

/** Hora de inicio/fin para un día UI (LUN, MAR, …) dentro del texto de horario BUAP. */
export function extractHoraParaDia(horario: string, diaUi: string): string {
  const texto = horario.trim();
  if (!texto) {
    return '';
  }

  const aliases = DIA_ALIASES[diaUi] ?? [];
  const segmentos = texto.split('/').map((s) => s.trim()).filter(Boolean);

  for (const segmento of segmentos) {
    const match = segmento.match(/^([A-ZÁÉÍÓÚ]+)\s+(.+)$/i);
    if (!match) {
      continue;
    }
    const codigoDia = match[1].toUpperCase();
    if (aliases.includes(codigoDia)) {
      return formatFranjaHorario(match[2].trim());
    }
  }

  const primeraFranja = texto.match(/(\d{3,4}\s*-\s*\d{3,4}|\d{1,2}:\d{2}(?:\s*-\s*\d{1,2}:\d{2})?)/);
  return primeraFranja ? formatFranjaHorario(primeraFranja[1]) : '';
}
