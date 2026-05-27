from django.test import RequestFactory, TestCase, override_settings

from apps.core.services import is_internal_api_key_valid


class InternalApiKeyValidationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(INTERNAL_API_KEY='clave-secreta')
    def test_internal_api_key_accepts_surrounding_spaces(self):
        request = self.factory.post(
            '/usuarios',
            HTTP_X_INTERNAL_API_KEY='  clave-secreta  ',
        )

        self.assertTrue(is_internal_api_key_valid(request))

    @override_settings(INTERNAL_API_KEY='clave-secreta')
    def test_internal_api_key_rejects_different_value(self):
        request = self.factory.post(
            '/usuarios',
            HTTP_X_INTERNAL_API_KEY='otra-clave',
        )

        self.assertFalse(is_internal_api_key_valid(request))