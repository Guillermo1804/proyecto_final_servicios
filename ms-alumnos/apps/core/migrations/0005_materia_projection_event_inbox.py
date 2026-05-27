from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_event_outbox_pending_users"),
    ]

    operations = [
        migrations.CreateModel(
            name="EventInbox",
            fields=[
                ("event_id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("event_name", models.CharField(db_index=True, max_length=128)),
                ("handler", models.CharField(max_length=64)),
                ("processed_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "event_inbox",
            },
        ),
        migrations.CreateModel(
            name="MateriaProjection",
            fields=[
                ("materia_id", models.IntegerField(primary_key=True, serialize=False)),
                ("periodo_id", models.IntegerField(db_index=True, default=0)),
                ("periodo_nombre", models.CharField(blank=True, default="", max_length=128)),
                ("nrc", models.CharField(default="", max_length=32)),
                ("nombre", models.CharField(default="", max_length=255)),
                ("seccion", models.CharField(blank=True, default="", max_length=32)),
                ("clave", models.CharField(blank=True, default="", max_length=32)),
                ("horario", models.CharField(blank=True, default="", max_length=255)),
                ("docente_id", models.IntegerField(blank=True, db_index=True, null=True)),
                ("docente_nombre", models.CharField(blank=True, default="", max_length=255)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "materia_projection",
            },
        ),
    ]
