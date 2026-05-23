"""Cursor global data_as_of para consistencia eventual de reportes."""

from __future__ import annotations

from datetime import datetime

from django.db.models import F
from django.utils import timezone

from apps.reportes.models import EventInbox, ReportAnalyticsState


def touch_data_as_of(at: datetime | None = None) -> datetime:
    ts = at or timezone.now()
    state, _ = ReportAnalyticsState.objects.get_or_create(pk=1)
    ReportAnalyticsState.objects.filter(pk=1).update(
        data_as_of=ts,
        events_processed=F('events_processed') + 1,
    )
    return ts


def get_data_as_of() -> datetime | None:
    state = ReportAnalyticsState.objects.filter(pk=1).first()
    if state and state.data_as_of:
        return state.data_as_of
    return (
        EventInbox.objects.order_by('-processed_at')
        .values_list('processed_at', flat=True)
        .first()
    )


def reset_analytics_state() -> None:
    ReportAnalyticsState.objects.update_or_create(
        pk=1,
        defaults={'data_as_of': None, 'events_processed': 0},
    )
