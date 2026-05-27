# Evidencia de entrega — Demo correo MS-6 (§6.3)

Checklist para el video o informe final. **No subir al repo** capturas que muestren contraseñas SMTP, `INTERNAL_API_KEY` ni tokens de reset completos.

## 1. Correo real en bandeja

```powershell
# Tras configurar SMTP en ms-notificaciones/.env
docker exec agm-ms-notificaciones python manage.py send_test_email --to TU_EMAIL@ejemplo.com
```

**Evidencia sugerida:** captura del cliente de correo (asunto AGM, cuerpo HTML) con datos personales censurados si aplica.

## 2. Registro en HistorialCorreo

**Opción A — Django Admin**

1. Abrir `http://localhost:8006/admin/`
2. Iniciar sesión con superusuario (`createsuperuser` si falta).
3. Entrar a **Historial correos** y mostrar fila con `exitoso=True`, tipo `bienvenida` o prueba SMTP.

**Opción B — Consola**

```powershell
docker exec agm-ms-notificaciones python manage.py shell -c "
from apps.notificaciones.models import HistorialCorreo
for h in HistorialCorreo.objects.order_by('-id')[:5]:
    print(h.id, h.tipo, h.destinatario_email, h.exitoso, h.enviado_en)
"
```

## 3. Flujo integrado (opcional en video)

| Paso | Acción | Qué mostrar |
|------|--------|-------------|
| 1 | Postman `POST {{base_url_gateway}}/notificaciones/bienvenida` con `X-Internal-Api-Key` | JSON `success: true` |
| 2 | MS-3 importar alumno | Log MS-3 + nuevo historial `bienvenida` |
| 3 | `POST /auth/forgot-password` | Historial `reset_password` |
| 4 | `POST /calificaciones/materias/5/cerrar` | Varios historial `cierre_materia` |

## 4. Auditoría Git (sin secretos)

```powershell
git grep -iE "EMAIL_HOST_PASSWORD|app-password" -- ":!*.example"
```

Solo deben aparecer referencias en documentación o `config()` / placeholders, nunca credenciales reales.

## 5. Producción documentada

En Railway / producción:

```env
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://tu-frontend,https://tu-gateway
```

Ver `ms-notificaciones/.env.example` y `DESPLIEGUE_RAILWAY.md`.
