# Evidencia Demo §6.3 — Exportación reporte (flujo docente)

Requisito del enunciado: demostrar exportación exitosa de **Excel o PDF** desde el flujo del docente.

## Archivos generados (2026-05-17)

| Archivo | Formato | Tamaño aprox. |
|---------|---------|---------------|
| `calificaciones_demo.xlsx` | Excel concentrado calificaciones | ~5 KB |
| `calificaciones_demo.pdf` | PDF concentrado calificaciones | ~2 KB |

Generados con la misma lógica de producción (`build_report_bytes` + `openpyxl` / `reportlab`) dentro del contenedor `agm-ms-reportes`.

## Reproducir con Postman (flujo docente en producción integrada)

1. Importar `docs/postman/AGM_API_Collection.json` y `AGM_Environment.json`.
2. Obtener JWT: `POST {{base_url_gateway}}/auth/login` (colección auth) con credenciales de docente o admin.
3. Copiar `access_token` → variable `jwt_token`.
4. Ajustar `materia_id` a una materia existente donde el docente sea titular.
5. Ejecutar **MS-7 → Calificaciones — Excel (xlsx)** o **Calificaciones — PDF**.
6. En Postman: **Send and Download** → guardar archivo.
7. Captura de pantalla para el video/manual: respuesta **200**, `Content-Disposition: attachment`, vista previa del archivo abierto.

## Reproducir con curl (admin)

```powershell
$login = Invoke-RestMethod -Uri "http://localhost:8001/auth/login" -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"admin@agm.buap.mx","password":"admin123"}'
$token = $login.data.access_token
Invoke-WebRequest -Uri "http://localhost:8080/reportes/calificaciones/MATERIA_ID?formato=xlsx" `
  -Headers @{ Authorization = "Bearer $token" } `
  -OutFile "calificaciones_export.xlsx"
```

> Sustituir `MATERIA_ID` por un ID válido en MS-2. Sin materias en BD, usar los archivos `*_demo.*` de esta carpeta como evidencia de generación binaria.

## Checklist video §6.3

- [ ] Login docente
- [ ] Navegación a reportes de una materia asignada
- [ ] Descarga Excel o PDF exitosa (200)
- [ ] Archivo abre con datos legibles (UTF-8 en PDF si aplica)
