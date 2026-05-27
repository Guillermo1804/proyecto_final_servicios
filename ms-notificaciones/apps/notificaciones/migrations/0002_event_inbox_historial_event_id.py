# Fase 5 MS-6 — inbox + trazabilidad historial

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notificaciones', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventInbox',
            fields=[
                ('event_id', models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ('event_name', models.CharField(db_index=True, max_length=128)),
                ('handler', models.CharField(max_length=64)),
                ('processed_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'event_inbox',
            },
        ),
        migrations.AddField(
            model_name='historialcorreo',
            name='event_id',
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='historialcorreo',
            name='estado_envio',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('sent', 'Sent'),
                    ('failed', 'Failed'),
                    ('retrying', 'Retrying'),
                    ('dead_letter', 'Dead letter'),
                ],
                db_index=True,
                default='pending',
                max_length=16,
            ),
        ),
        migrations.AddIndex(
            model_name='historialcorreo',
            index=models.Index(
                fields=['event_id', 'destinatario_email'],
                name='idx_historial_event_dest',
            ),
        ),
    ]
