# Generated manually — Fase 7 MS-5

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventOutbox',
            fields=[
                ('event_id', models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ('event_name', models.CharField(max_length=128)),
                ('event_version', models.PositiveIntegerField(default=1)),
                ('aggregate_type', models.CharField(max_length=64)),
                ('aggregate_id', models.CharField(max_length=64)),
                ('payload', models.JSONField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('published', 'Published'), ('failed', 'Failed')], db_index=True, default='pending', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('retry_count', models.PositiveIntegerField(default=0)),
                ('last_error', models.TextField(blank=True, null=True)),
            ],
            options={'db_table': 'event_outbox'},
        ),
        migrations.CreateModel(
            name='EventInbox',
            fields=[
                ('event_id', models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ('event_name', models.CharField(db_index=True, max_length=128)),
                ('handler', models.CharField(max_length=64)),
                ('processed_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'event_inbox'},
        ),
        migrations.CreateModel(
            name='PeriodoProjection',
            fields=[
                ('periodo_id', models.IntegerField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(default='', max_length=100)),
                ('activo', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'periodo_projection'},
        ),
        migrations.CreateModel(
            name='MateriaProjection',
            fields=[
                ('materia_id', models.IntegerField(primary_key=True, serialize=False)),
                ('periodo_id', models.IntegerField(db_index=True)),
                ('nrc', models.CharField(default='', max_length=32)),
                ('nombre', models.CharField(default='', max_length=255)),
                ('docente_id', models.IntegerField(blank=True, null=True)),
                ('periodo_activo', models.BooleanField(default=True)),
                ('cerrada_upstream', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'materia_projection'},
        ),
        migrations.CreateModel(
            name='AlumnoProjection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alumno_id', models.IntegerField(db_index=True)),
                ('materia_id', models.IntegerField(db_index=True)),
                ('matricula', models.CharField(default='', max_length=32)),
                ('nombre', models.CharField(default='', max_length=255)),
                ('email', models.EmailField(blank=True, default='', max_length=254)),
                ('activa', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'alumno_projection'},
        ),
        migrations.AddIndex(
            model_name='eventoutbox',
            index=models.Index(fields=['status', 'created_at'], name='idx_ms5_outbox_status'),
        ),
        migrations.AddConstraint(
            model_name='alumnoprojection',
            constraint=models.UniqueConstraint(fields=('alumno_id', 'materia_id'), name='uniq_alumno_projection_materia'),
        ),
    ]
