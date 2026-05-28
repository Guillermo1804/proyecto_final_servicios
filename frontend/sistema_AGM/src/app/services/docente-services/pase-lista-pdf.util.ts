import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

import { ContextoMateriaSesion, RegistroAsistencia } from './asistencias-docente.service';

export function descargarPaseListaPdf(
  registros: RegistroAsistencia[],
  materia: ContextoMateriaSesion,
  sesionId: number,
  fechaSesion?: string,
): void {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'letter' });
  const fecha =
    fechaSesion?.slice(0, 10) ?? new Date().toISOString().slice(0, 10);
  const titulo = `Pase de lista — ${materia.clave} ${materia.materia}`;
  const subtitulo = `Grupo ${materia.seccion} | NRC ${materia.nrc} | Sesi\u00f3n ${sesionId} | ${fecha}`;

  doc.setFontSize(14);
  doc.text(titulo, 14, 18);
  doc.setFontSize(10);
  doc.text(subtitulo, 14, 26);
  doc.text(`Sal\u00f3n: ${materia.salon}`, 14, 32);

  const filas = registros.map((r) => [r.nombre, r.estado, r.hora, String(r.minuto)]);

  autoTable(doc, {
    startY: 38,
    head: [['Nombre', 'Estado', 'Hora', 'Minuto']],
    body: filas.length > 0 ? filas : [['(sin registros)', '', '', '']],
    styles: { fontSize: 9, cellPadding: 2 },
    headStyles: { fillColor: [7, 95, 198] },
  });

  const presentes = registros.filter((r) => r.estado === 'PRESENTE').length;
  const retardos = registros.filter((r) => r.estado === 'RETARDO').length;
  const finalY = (doc as jsPDF & { lastAutoTable?: { finalY: number } }).lastAutoTable?.finalY ?? 50;
  doc.setFontSize(9);
  doc.text(
    `Total: ${registros.length} | Presentes: ${presentes} | Retardos: ${retardos}`,
    14,
    finalY + 8,
  );

  doc.save(`pase_lista_${materia.clave}_sesion${sesionId}_${fecha}.pdf`);
}
