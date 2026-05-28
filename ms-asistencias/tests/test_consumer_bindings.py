from django.test import SimpleTestCase

from agm_events.consumer_bindings import missing_handlers

from apps.core.event_bus.consumers import HANDLERS


class ConsumerBindingsTests(SimpleTestCase):
    def test_ms_asistencias_handlers_cover_catalog(self):
        missing = missing_handlers('ms-asistencias', HANDLERS)
        self.assertEqual(
            missing,
            [],
            f'Faltan handlers en MS-5: {missing}. Ver contracts/events/consumer_bindings.json',
        )
