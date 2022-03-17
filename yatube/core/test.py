from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus


User = get_user_model()


class CoreTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='auth')
        self.guest_client = Client()

    def test_unexisting_page_exist(self):
        """Проверяем несуществующую страницу."""

        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
