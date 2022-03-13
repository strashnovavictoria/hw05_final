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

        cls.templates_page_names_create = {
            reverse('posts:post_create'):
                'posts/post_create.html',
            reverse('posts:post_edit', kwargs={'post_id': cls.post.id}):
                'posts/post_edit.html'
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
                # Проверка, что есть группа.
                self.assertEqual(post_group, self.post.group)
                # Проверка, что этот пост не попал в группу,
                #  для которой не был предназначен.
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

    def test_index_cached(self):
        """Проверяем кэш."""
        response = self.authorized_client.get(reverse("posts:index"))
        resp1 = response.content
        delete_post = Post.objects.get(id=1)
        delete_post.delete()
        response2 = self.authorized_client.get(reverse("posts:index"))
        resp2 = response2.content
        self.assertTrue(resp1 != resp2)

    def test_follow(self):
        """Проверка подписки на автора."""
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        self.assertEqual(Follow.objects.count(), 1)
        Follow.objects.all().delete()
        self.assertEqual(Follow.objects.count(), 0)


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
