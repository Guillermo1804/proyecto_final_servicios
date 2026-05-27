# Generated manually — Fase 2 bus de eventos

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EventOutbox",
            fields=[
                (
                    "event_id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
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
                "verbose_name": "Evento outbox",
                "verbose_name_plural": "Eventos outbox",
                "db_table": "event_outbox",
                "indexes": [
                    models.Index(
                        fields=["status", "created_at"],
                        name="idx_outbox_status_created",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="EventInbox",
            fields=[
                (
                    "event_id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("event_name", models.CharField(max_length=128)),
                ("processed_at", models.DateTimeField(auto_now_add=True)),
                ("handler", models.CharField(max_length=128)),
            ],
            options={
                "verbose_name": "Evento inbox",
                "verbose_name_plural": "Eventos inbox",
                "db_table": "event_inbox",
            },
        ),
    ]
