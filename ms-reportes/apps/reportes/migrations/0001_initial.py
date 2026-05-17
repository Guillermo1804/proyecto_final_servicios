# Generated manually for Fase A (ISSUE-901)

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ReporteGenerado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'tipo',
                    models.CharField(
                        choices=[('calificaciones', 'Calificaciones'), ('asistencias', 'Asistencias')],
                        max_length=20,
                    ),
                ),
                ('usuario_id', models.IntegerField(help_text='usuario_id del solicitante (MS-1)')),
                (
                    'formato',
                    models.CharField(
                        choices=[('xlsx', 'Excel'), ('pdf', 'PDF')],
                        max_length=10,
                    ),
                ),
                ('generado_en', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'reporte_generado',
                'ordering': ['-generado_en'],
                'indexes': [
                    models.Index(fields=['usuario_id', 'generado_en'], name='idx_reporte_usuario_fecha'),
                    models.Index(fields=['tipo', 'generado_en'], name='idx_reporte_tipo_fecha'),
                ],
            },
        ),
    ]
