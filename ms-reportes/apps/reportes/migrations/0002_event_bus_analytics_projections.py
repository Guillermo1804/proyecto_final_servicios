# Generated for Fase 8 — MS-7 event bus + proyecciones analíticas

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reportes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventInbox',
            fields=[
                ('event_id', models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ('event_name', models.CharField(db_index=True, max_length=128)),
                ('handler', models.CharField(max_length=64)),
                ('processed_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'db_table': 'event_inbox',
            },
        ),
        migrations.CreateModel(
            name='ReportAnalyticsState',
            fields=[
                ('id', models.PositiveSmallIntegerField(default=1, primary_key=True, serialize=False)),
                ('data_as_of', models.DateTimeField(blank=True, null=True)),
                ('events_processed', models.PositiveIntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'report_analytics_state',
            },
        ),
        migrations.CreateModel(
            name='ReportePeriodoProjection',
            fields=[
                ('periodo_id', models.IntegerField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(default='', max_length=128)),
                ('activo', models.BooleanField(db_index=True, default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'reporte_periodo_projection',
            },
        ),
        migrations.CreateModel(
            name='ReporteMateriaProjection',
            fields=[
                ('materia_id', models.IntegerField(primary_key=True, serialize=False)),
                ('periodo_id', models.IntegerField(db_index=True)),
                ('periodo_nombre', models.CharField(default='', max_length=128)),
                ('nrc', models.CharField(db_index=True, default='', max_length=32)),
                ('nombre', models.CharField(default='', max_length=255)),
                ('seccion', models.CharField(default='', max_length=32)),
                ('clave', models.CharField(default='', max_length=32)),
                ('docente_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('docente_nombre', models.CharField(default='', max_length=255)),
                ('horario', models.CharField(default='', max_length=128)),
                ('cerrada', models.BooleanField(db_index=True, default=False)),
                ('total_alumnos', models.PositiveIntegerField(default=0)),
                ('aprobados', models.PositiveIntegerField(default=0)),
                ('reprobados', models.PositiveIntegerField(default=0)),
                ('promedio_grupal', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('total_sesiones_qr', models.PositiveIntegerField(default=0)),
                ('porcentaje_asistencia_grupal', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'reporte_materia_projection',
                'indexes': [
                    models.Index(fields=['docente_id', 'periodo_id'], name='idx_rep_mat_doc_per'),
                ],
            },
        ),
        migrations.CreateModel(
            name='ReporteAlumnoProjection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alumno_id', models.IntegerField(db_index=True)),
                ('materia_id', models.IntegerField(db_index=True)),
                ('usuario_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('matricula', models.CharField(default='', max_length=32)),
                ('nombre', models.CharField(default='', max_length=255)),
                ('email', models.EmailField(default='')),
                ('activa', models.BooleanField(db_index=True, default=True)),
                ('promedio_real', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('promedio_redondeado', models.SmallIntegerField(default=0)),
                ('presentes', models.PositiveIntegerField(default=0)),
                ('retardos', models.PositiveIntegerField(default=0)),
                ('ausentes', models.PositiveIntegerField(default=0)),
                ('porcentaje_asistencia', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'reporte_alumno_projection',
                'indexes': [
                    models.Index(fields=['materia_id', 'activa'], name='idx_rep_alu_mat_act'),
                    models.Index(fields=['alumno_id', 'activa'], name='idx_rep_alu_alu_act'),
                ],
                'constraints': [
                    models.UniqueConstraint(fields=('alumno_id', 'materia_id'), name='uniq_reporte_alumno_materia'),
                ],
            },
        ),
        migrations.CreateModel(
            name='ReporteCalificacionProjection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('actividad_id', models.IntegerField(db_index=True)),
                ('alumno_id', models.IntegerField(db_index=True)),
                ('materia_id', models.IntegerField(db_index=True)),
                ('calificacion_id', models.IntegerField(blank=True, null=True)),
                ('categoria', models.CharField(default='', max_length=128)),
                ('porcentaje_categoria', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('actividad_nombre', models.CharField(default='', max_length=255)),
                ('calificacion', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'reporte_calificacion_projection',
                'indexes': [
                    models.Index(fields=['materia_id', 'categoria'], name='idx_rep_cal_mat_cat'),
                ],
                'constraints': [
                    models.UniqueConstraint(fields=('actividad_id', 'alumno_id'), name='uniq_reporte_calif_act_alu'),
                ],
            },
        ),
        migrations.CreateModel(
            name='ReporteAsistenciaProjection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sesion_id', models.IntegerField()),
                ('materia_id', models.IntegerField(db_index=True)),
                ('alumno_id', models.IntegerField(db_index=True)),
                ('estado', models.CharField(max_length=16)),
                ('minuto_registro', models.SmallIntegerField(default=0)),
                ('registro_id', models.IntegerField(blank=True, null=True)),
                ('registrado_en', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'reporte_asistencia_projection',
                'constraints': [
                    models.UniqueConstraint(fields=('sesion_id', 'alumno_id'), name='uniq_reporte_asist_ses_alu'),
                ],
            },
        ),
    ]
