from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reportes', '0002_event_bus_analytics_projections'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReporteDocenteProjection',
            fields=[
                ('docente_id', models.IntegerField(primary_key=True, serialize=False)),
                ('usuario_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('email', models.EmailField(db_index=True)),
                ('nombre', models.CharField(blank=True, default='', max_length=255)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'reporte_docente_projection',
            },
        ),
    ]
