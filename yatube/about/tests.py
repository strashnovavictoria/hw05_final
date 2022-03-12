from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, Client
from http import HTTPStatus


User = get_user_model()


class AboutURLTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='auth')
        self.guest_client = Client()

    def test_urls_correct_template(self):
        templates = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }

        for reverse_name, template in templates.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)
