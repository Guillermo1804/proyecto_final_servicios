from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ponderacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('materia_id', models.IntegerField(db_index=True)),
                ('nombre_categoria', models.CharField(max_length=100)),
                ('porcentaje', models.DecimalField(decimal_places=2, max_digits=5)),
            ],
            options={
                'verbose_name': 'Ponderación',
                'verbose_name_plural': 'Ponderaciones',
                'ordering': ['id'],
            },
        ),
        migrations.AddConstraint(
            model_name='ponderacion',
            constraint=models.UniqueConstraint(fields=('materia_id', 'nombre_categoria'), name='uniq_ponderacion_materia_categoria'),
        ),
        migrations.CreateModel(
            name='Actividad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('descripcion', models.TextField(blank=True)),
                ('fecha', models.DateField(blank=True, null=True)),
                ('ponderacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actividades', to='core.ponderacion')),
            ],
            options={
                'verbose_name': 'Actividad',
                'verbose_name_plural': 'Actividades',
            },
        ),
        migrations.CreateModel(
            name='Calificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alumno_id', models.IntegerField(db_index=True)),
                ('calificacion', models.DecimalField(decimal_places=2, max_digits=4)),
                ('fecha_asignacion', models.DateTimeField(auto_now=True)),
                ('actividad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calificaciones', to='core.actividad')),
            ],
            options={
                'verbose_name': 'Calificación',
                'verbose_name_plural': 'Calificaciones',
            },
        ),
        migrations.AddConstraint(
            model_name='calificacion',
            constraint=models.UniqueConstraint(fields=('actividad', 'alumno_id'), name='uniq_calificacion_actividad_alumno'),
        ),
    ]