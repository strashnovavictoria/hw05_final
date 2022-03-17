import shutil
import tempfile

from posts.models import Post, Group, User, Follow
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст для тестового поста',
            group=cls.group,
            image=cls.uploaded
        )
        cls.templates_page_names = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:profile', kwargs={'username': cls.user}):
                'posts/profile.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html'
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):

        self.guest_client = Client()
        self.authorized_client = Client()

    def test_pages_uses_correct_template(self):
        """Проверка какие вызываются шаблоны, при вызове вью через name."""
        for reverse_name, template in self.templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом."""
        for reverse_name, template in self.templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post_object = response.context['page_obj'][0]
                post_text = post_object.text
                self.assertEqual(post_text, 'Текст для тестового поста')
                post_author = post_object.author
                self.assertEqual(post_author, self.post.author)
                post_group = post_object.group
                self.assertEqual(post_group, self.post.group)

    def test_pages_show_correct_group(self):
        """При создании группа появляется на главной странице,
            на странице группы."""
        templates_index_postlist = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html'}

        for reverse_name, template in templates_index_postlist.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post_object = response.context['page_obj'][0]
                post_group = post_object.group
                self.assertEqual(post_group, self.post.group)
                self.assertEqual(post_object.group.title, 'Тестовая группа')
                self.assertEqual(post_group.slug, 'test-slug')
                self.assertEqual(post_group.description, 'Тестовое описание')

    def test_pages_show_image(self):
        """При создании картинка появляется на главной странице,
            на странице группы и автора"""
        for reverse_name, template in self.templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post_object = response.context['page_obj'][0]
                post_image = post_object.image
                self.assertEqual(post_image, self.post.image)

    def test_pages_show_image_detail(self):
        """При создании картинка появляется на странице поста."""
        adress = reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        response = self.authorized_client.get(adress)
        post_object = response.context['post']
        post_image = post_object.image
        self.assertEqual(post_image, self.post.image)


class PaginatorViewsTest(TestCase):
    """Проверка Paginator."""

    page_contains_three = 3
    page_contains_ten = 10

    def setUp(self):
        user = User.objects.create(username='auth')
        group = Group.objects.create(
            title='slug-group',
            slug='slug-test'
        )
        for i in range(0, 13):
            Post.objects.create(
                author=user,
                group=group
            )

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         self.page_contains_ten)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         self.page_contains_three)


class CacheViewsTest(TestCase):
    """Тест кэша."""

    def setUp(self):
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()

        self.post = Post.objects.create(
            author=self.user,
            text='Текст для тестового поста',
        )

    def test_index_cache(self):
        """Проверяем кэш на главной странице."""

        response = self.authorized_client.get(reverse("posts:index"))
        resp1 = response.content
        delete_post = Post.objects.get(id=1)
        delete_post.delete()
        response2 = self.authorized_client.get(reverse("posts:index"))
        resp2 = response2.content
        self.assertTrue(resp1 != resp2)


class FollowTest(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username='follower')
        self.user2 = User.objects.create_user(username='author')
        self.user3 = User.objects.create_user(username='guest')

        self.authorized_client = Client()
        self.guest_client = Client()

        self.post = Post.objects.create(
            author=self.user2,
            text='Текст для тестового поста',
        )

    def test_follower(self):
        """Проверка подписки."""

        adress = reverse('posts:profile', kwargs={'username': self.user2})
        response_profile = self.authorized_client.get(adress)
        self.assertIn('Подписаться', response_profile.content.decode())
        self.assertNotIn('Отписаться', response_profile.content.decode())

        Follow.objects.get_or_create(user=self.user1, author=self.user2)
        subscribe_follow = Follow.objects.filter(user=self.user1,
                                                 author=self.user2)
        self.assertEqual(subscribe_follow.count(), 1)

        not_subscribe_follow = Follow.objects.filter(user=self.user3,
                                                     author=self.user2)
        self.assertEqual(not_subscribe_follow.count(), 0)
