from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        'Название',
        help_text='Введите название поста',
        max_length=200
    )
    slug = models.SlugField(
        'URL',
        help_text='Введите URL поста',
        max_length=200,
        unique=True
    )
    description = models.TextField(
        'Описание',
        help_text='Введите oписание поста'
    )

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )

    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        related_name='comments',
        on_delete=models.CASCADE
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите текст комментария'
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self) -> str:
        return self.text

    class Meta:
        ordering = ['-created']


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=None,
        related_name='follower',
        verbose_name='Юзер'
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE,
        verbose_name='Aвтор'
    )
