# Generated manually — restores migration chain for ms-alumnos

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Docente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usuario_id', models.IntegerField(help_text='ID en MS-1 Auth', unique=True)),
                ('nombre', models.CharField(max_length=255)),
                ('apellido', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('departamento', models.CharField(blank=True, max_length=255)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Docente',
                'verbose_name_plural': 'Docentes',
            },
        ),
        migrations.CreateModel(
            name='Alumno',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usuario_id', models.IntegerField(help_text='ID en MS-1 Auth', unique=True)),
                ('matricula', models.CharField(max_length=20, unique=True)),
                ('nombre', models.CharField(max_length=255)),
                ('apellido', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254)),
                ('carrera', models.CharField(blank=True, max_length=100)),
                ('semestre', models.IntegerField(default=1)),
                ('activo', models.BooleanField(default=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Alumno',
                'verbose_name_plural': 'Alumnos',
            },
        ),
        migrations.CreateModel(
            name='InscripcionMateria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('materia_id', models.IntegerField(help_text='ID en MS-2 Periodos')),
                ('nrc', models.CharField(max_length=20)),
                ('nombre_materia', models.CharField(max_length=255)),
                ('docente_nombre', models.CharField(max_length=255)),
                ('horario', models.CharField(blank=True, max_length=255)),
                ('activa', models.BooleanField(default=True)),
                ('fecha_inscripcion', models.DateTimeField(auto_now_add=True)),
                (
                    'alumno',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='inscripciones',
                        to='core.alumno',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Inscripción de Materia',
                'verbose_name_plural': 'Inscripciones de Materias',
            },
        ),
    ]
