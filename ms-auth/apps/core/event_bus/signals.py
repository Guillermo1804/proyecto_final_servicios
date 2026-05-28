"""Señales de dominio de usuario → outbox."""

from __future__ import annotations

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.core.event_bus.outbox import enqueue_domain_event
from apps.core.models import User


def _user_payload(user: User) -> dict:
    return {
        "user_id": user.id,
        "email": user.email,
        "nombre": user.nombre,
        "rol": user.rol,
        "activo": user.activo,
    }


@receiver(pre_save, sender=User)
def capture_user_previous_state(sender, instance: User, **kwargs) -> None:
    if not instance.pk:
        instance._event_previous_rol = None
        instance._event_previous_activo = None
        return
    try:
        previous = User.objects.only("rol", "activo").get(pk=instance.pk)
        instance._event_previous_rol = previous.rol
        instance._event_previous_activo = previous.activo
    except User.DoesNotExist:
        instance._event_previous_rol = None
        instance._event_previous_activo = None


@receiver(post_save, sender=User)
def emit_user_lifecycle_events(sender, instance: User, created: bool, **kwargs) -> None:
    payload = _user_payload(instance)

    if created:
        enqueue_domain_event(
            event_name="user.created.v1",
            aggregate_type="user",
            aggregate_id=str(instance.pk),
            payload=payload,
        )
        return

    previous_rol = getattr(instance, "_event_previous_rol", None)
    previous_activo = getattr(instance, "_event_previous_activo", None)

    if previous_activo is True and instance.activo is False:
        enqueue_domain_event(
            event_name="user.deactivated.v1",
            aggregate_type="user",
            aggregate_id=str(instance.pk),
            payload=payload,
        )
        return

    if previous_rol is not None and previous_rol != instance.rol:
        enqueue_domain_event(
            event_name="user.role_changed.v1",
            aggregate_type="user",
            aggregate_id=str(instance.pk),
            payload={
                **payload,
                "previous_rol": previous_rol,
                "new_rol": instance.rol,
            },
        )
        return

    enqueue_domain_event(
        event_name="user.updated.v1",
        aggregate_type="user",
        aggregate_id=str(instance.pk),
        payload=payload,
    )
