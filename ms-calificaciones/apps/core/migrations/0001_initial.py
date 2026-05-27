from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='EstadoMateria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('materia_id', models.IntegerField(unique=True)),
                ('cerrada', models.BooleanField(default=False)),
                ('lista_impresa', models.BooleanField(default=False)),
                ('fecha_cierre', models.DateTimeField(blank=True, null=True)),
                ('notificacion_enviada', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Estado de materia',
                'verbose_name_plural': 'Estados de materias',
            },
        ),
    ]
