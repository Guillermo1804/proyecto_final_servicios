# Generated manually — Fase 4 MS-3

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_inscripcion_fecha_baja"),
    ]

    operations = [
        migrations.AlterField(
            model_name="alumno",
            name="usuario_id",
            field=models.IntegerField(
                blank=True,
                help_text="ID en MS-1 Auth (null mientras pending_user_creation)",
                null=True,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="docente",
            name="usuario_id",
            field=models.IntegerField(
                blank=True,
                help_text="ID en MS-1 Auth (null mientras pending_user_creation)",
                null=True,
                unique=True,
            ),
        ),
        migrations.CreateModel(
            name="PendingUserCreation",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "entity_type",
                    models.CharField(
                        choices=[("alumno", "Alumno"), ("docente", "Docente")],
                        max_length=16,
                    ),
                ),
                ("entity_id", models.PositiveIntegerField()),
                ("email", models.EmailField(max_length=254)),
                ("nombre", models.CharField(max_length=255)),
                ("rol", models.CharField(max_length=32)),
                ("temporary_password", models.CharField(max_length=128)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("ms1_user_id", models.IntegerField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "pending_user_creation",
                "indexes": [
                    models.Index(
                        fields=["entity_type", "entity_id"],
                        name="idx_pending_entity",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="EventOutbox",
            fields=[
                ("event_id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("event_name", models.CharField(max_length=128)),
                ("event_version", models.PositiveIntegerField(default=1)),
                ("aggregate_type", models.CharField(max_length=64)),
                ("aggregate_id", models.CharField(max_length=64)),
                ("payload", models.JSONField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("published", "Published"),
                            ("failed", "Failed"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("retry_count", models.PositiveIntegerField(default=0)),
                ("last_error", models.TextField(blank=True, null=True)),
            ],
            options={
                "db_table": "event_outbox",
                "indexes": [
                    models.Index(
                        fields=["status", "created_at"],
                        name="idx_outbox_status_created",
                    )
                ],
            },
        ),
    ]
