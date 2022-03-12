from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Post, Group, User
from http import HTTPStatus


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст для тестового поста',
        )

        cls.guest_URL_templates = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{PostsURLTests.post.id}/': 'posts/post_detail.html',
        }

        cls.authorized_URL_templates = {
            f'/posts/{PostsURLTests.post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)

    def test_urls_guest_correct_template(self):
        """Проверяем публичные адреса."""
        for address, template in self.guest_URL_templates.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized_correct_template(self):
        """Проверяем приватные адреса."""
        for address, template in self.authorized_URL_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_url_exist(self):
        """Проверяем несуществующую страницу."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_authorized_client_can_post(self):
        """Только авторизованный пользователь может написать пост."""
        response = self.guest_client.get(
            reverse('posts:post_create'))
        self.assertEqual(
            response.url,
            f'{reverse("users:login")}'
            f'?next='
            f'{reverse("posts:post_create")}')
