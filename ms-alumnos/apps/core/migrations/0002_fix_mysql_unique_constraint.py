from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE core_inscripcionmateria ADD UNIQUE INDEX unique_inscripcion_activa_mysql (alumno_id, materia_id, (CASE WHEN activa THEN 1 ELSE NULL END));",
            reverse_sql="ALTER TABLE core_inscripcionmateria DROP INDEX unique_inscripcion_activa_mysql;"
        ),
    ]
