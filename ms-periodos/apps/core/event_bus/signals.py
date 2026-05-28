"""Señales Periodo/Materia → outbox."""

from __future__ import annotations

from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from apps.core.event_bus.outbox import enqueue_domain_event
from apps.core.event_bus.payloads import materia_payload, periodo_payload
from apps.core.models import Materia, Periodo


@receiver(pre_save, sender=Periodo)
def periodo_pre_save(sender, instance: Periodo, **kwargs) -> None:
    if not instance.pk:
        instance._prev_activo = None
        return
    try:
        prev = Periodo.objects.only("activo").get(pk=instance.pk)
        instance._prev_activo = prev.activo
    except Periodo.DoesNotExist:
        instance._prev_activo = None


@receiver(post_save, sender=Periodo)
def periodo_post_save(sender, instance: Periodo, created: bool, **kwargs) -> None:
    payload = periodo_payload(instance)
    if created:
        enqueue_domain_event(
            event_name="periodo.created.v1",
            aggregate_type="periodo",
            aggregate_id=str(instance.pk),
            payload=payload,
        )
        return

    prev_activo = getattr(instance, "_prev_activo", None)
    if prev_activo is False and instance.activo is True:
        enqueue_domain_event(
            event_name="periodo.activated.v1",
            aggregate_type="periodo",
            aggregate_id=str(instance.pk),
            payload=payload,
        )
        return
    if prev_activo is True and instance.activo is False:
        enqueue_domain_event(
            event_name="periodo.closed.v1",
            aggregate_type="periodo",
            aggregate_id=str(instance.pk),
            payload=payload,
        )
        return

    enqueue_domain_event(
        event_name="periodo.updated.v1",
        aggregate_type="periodo",
        aggregate_id=str(instance.pk),
        payload=payload,
    )


@receiver(pre_delete, sender=Periodo)
def periodo_pre_delete(sender, instance: Periodo, **kwargs) -> None:
    enqueue_domain_event(
        event_name="periodo.closed.v1",
        aggregate_type="periodo",
        aggregate_id=str(instance.pk),
        payload=periodo_payload(instance),
    )


@receiver(pre_save, sender=Materia)
def materia_pre_save(sender, instance: Materia, **kwargs) -> None:
    if not instance.pk:
        instance._prev_docente_id = None
        instance._prev_docente_nombre = None
        return
    try:
        prev = Materia.objects.only("docente_id", "docente_nombre").get(pk=instance.pk)
        instance._prev_docente_id = prev.docente_id
        instance._prev_docente_nombre = prev.docente_nombre
    except Materia.DoesNotExist:
        instance._prev_docente_id = None
        instance._prev_docente_nombre = None


@receiver(post_save, sender=Materia)
def materia_post_save(sender, instance: Materia, created: bool, **kwargs) -> None:
    payload = materia_payload(instance)
    if created:
        enqueue_domain_event(
            event_name="materia.created.v1",
            aggregate_type="materia",
            aggregate_id=str(instance.pk),
            payload=payload,
        )
        return

    prev_docente_id = getattr(instance, "_prev_docente_id", None)
    prev_docente_nombre = getattr(instance, "_prev_docente_nombre", None)
    docente_changed = (
        prev_docente_id != instance.docente_id
        or prev_docente_nombre != instance.docente_nombre
    )
    if docente_changed:
        enqueue_domain_event(
            event_name="materia.assigned_teacher.v1",
            aggregate_type="materia",
            aggregate_id=str(instance.pk),
            payload={
                **payload,
                "previous_docente_id": prev_docente_id,
                "previous_docente_nombre": prev_docente_nombre,
            },
        )
        return

    enqueue_domain_event(
        event_name="materia.updated.v1",
        aggregate_type="materia",
        aggregate_id=str(instance.pk),
        payload=payload,
    )


@receiver(pre_delete, sender=Materia)
def materia_pre_delete(sender, instance: Materia, **kwargs) -> None:
    enqueue_domain_event(
        event_name="materia.closed.v1",
        aggregate_type="materia",
        aggregate_id=str(instance.pk),
        payload=materia_payload(instance),
    )
