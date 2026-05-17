# Generated manually for ISSUE-801 (Fase A)

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='HistorialCorreo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'tipo',
                    models.CharField(
                        choices=[
                            ('bienvenida', 'Bienvenida'),
                            ('baja', 'Baja'),
                            ('cierre_materia', 'Cierre de materia'),
                            ('reset_password', 'Reset de contraseña'),
                        ],
                        max_length=32,
                    ),
                ),
                ('destinatario_email', models.EmailField(max_length=254)),
                ('asunto', models.CharField(max_length=255)),
                ('cuerpo', models.TextField()),
                ('enviado_en', models.DateTimeField(auto_now_add=True)),
                ('exitoso', models.BooleanField(default=False)),
                ('error_msg', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'historial_correo',
                'ordering': ['-enviado_en'],
                'indexes': [
                    models.Index(fields=['tipo', 'enviado_en'], name='idx_historial_tipo_enviado'),
                ],
            },
        ),
    ]
