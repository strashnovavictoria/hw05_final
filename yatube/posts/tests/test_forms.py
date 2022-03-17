import shutil
import tempfile

from posts.models import Post, Group, User, Comment
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from http import HTTPStatus
from posts.forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
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
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.guest_client = Client()

    def test_form_post_create(self):
        """Проверяем,что создаётся новая запись в базе данных."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст для тестового поста',
            'group': PostCreateFormTest.group.id,
            'author': self.user,
            'image': self.uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Текст для тестового поста'
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                author=self.user
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_form_post_edit(self):
        """Проверяем,происходит изменение поста в базе данных, редирект."""
        old_post_text = PostCreateFormTest.post.text
        form_data = {
            'text': 'new_text',
            'group': PostCreateFormTest.group.id,
            'author': self.user,
            'image': self.uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        new_post_text = self.authorized_client.post
        self.assertNotEqual(new_post_text, old_post_text)
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.id}/edit/')

    def test_comments(self):
        """Проверяем,что создаётся новый комментарий в базе данных."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Текст для тестового комментария'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/'
                             f'{self.post.id}/comment/')
