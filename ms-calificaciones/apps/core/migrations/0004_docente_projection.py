from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_event_bus_projections'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocenteProjection',
            fields=[
                ('docente_id', models.IntegerField(primary_key=True, serialize=False)),
                ('usuario_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('email', models.EmailField(db_index=True)),
                ('nombre', models.CharField(blank=True, default='', max_length=255)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'docente_projection',
            },
        ),
    ]
