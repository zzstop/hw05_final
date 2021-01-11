from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Group(models.Model):
    title = models.CharField('название группы', max_length=200)
    slug = models.SlugField('слаг', unique=True)
    description = models.TextField('описание')

    class Meta:
        verbose_name = 'группа'
        verbose_name_plural = 'группы'

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        'текст', help_text='Перед публикацией заполните поле.')
    pub_date = models.DateTimeField(
        'дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='posts', verbose_name='автор')
    group = models.ForeignKey(
        Group, models.SET_NULL, blank=True,
        null=True, related_name='posts', verbose_name='группа',
        help_text='Выберите группу для публикации поста.')
    image = models.ImageField(
        'картинка', upload_to='posts/', blank=True, null=True,
        help_text='Выберите картинку для публикации поста.')

    class Meta:
        verbose_name = 'пост'
        verbose_name_plural = 'посты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        related_name='comments', verbose_name='пост')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='comments', verbose_name='автор')
    text = models.TextField(
        'текст комментария', help_text='Перед публикацией заполните поле.')
    created = models.DateTimeField(
        'дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
        ordering = ['-created']

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='follower', verbose_name='подписчик')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='following', verbose_name='автор')

    class Meta:
        UniqueConstraint(
            name='unique_follow',
            fields=['user', 'author'],
        )
