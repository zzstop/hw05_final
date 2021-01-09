import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.author = User.objects.create_user(username='Artur')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.author,
            group=self.group,
            image=PostPagesTests.uploaded
        )
        self.project_page = {
            'index': reverse('posts:index'),
            'group_posts': reverse(
                'posts:group_posts', kwargs={'slug': self.group.slug}),
            'new_post': reverse('posts:new_post'),
            'profile': reverse('posts:profile', kwargs={
                'username': self.author.username}),
            'post': reverse('posts:post', kwargs={
                'username': self.author.username, 'post_id': self.post.pk}),
            'post_edit': reverse('posts:post_edit', kwargs={
                'username': self.author.username, 'post_id': self.post.pk}),
            'profile_follow': reverse('posts:profile_follow', kwargs={
                'username': self.author.username}),
            'profile_unfollow': reverse('posts:profile_unfollow', kwargs={
                'username': self.author.username}),
        }
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_pages_use_correct_template(self):
        """Pages use appropriate template."""
        templates_pages_names = {
            'index.html': (self.project_page['index'],),
            'group.html': (self.project_page['group_posts'],),
            'profile.html': (self.project_page['profile'],),
            'post.html': (self.project_page['post'],),
            'new_post.html': (
                self.project_page['new_post'],
                self.project_page['post_edit'],)
        }
        for template, reverse_name in templates_pages_names.items():
            for url_name in reverse_name:
                with self.subTest(value=reverse_name):
                    response = self.authorized_client.get(url_name)
                    self.assertTemplateUsed(
                        response, template,
                        f'На страницу "{url_name}" view выводит '
                        f'неверный шаблон, требуется {template}.')

    def test_post_page_show_correct_context(self):
        """"
        Template 'post' contain correct context.
        """
        response = self.authorized_client.get(
            self.project_page['post'])
        current_context = response.context['post']
        expect_context = self.post
        self.assertEqual(
            current_context, expect_context,
            'Новый пост не попадает на страницу "post".')

    def test_pages_with_list_of_posts_show_correct_context(self):
        """"
        Templates contain correct context.
        Also check that the post get to the 'index' and 'profile' page
        when the group is selected.
        """
        pages = (
            self.project_page['index'],
            self.project_page['profile'],
        )
        expect_context = self.post
        for page in pages:
            with self.subTest(value=page):
                response = self.authorized_client.get(page)
                current_context = response.context['page'][0]
                self.assertEqual(
                    current_context, expect_context,
                    f'Новый пост не попадает на страницу {page}.')

    def test_group_page_show_correct_context(self):
        """
        Template 'group' contain correct context.
        Also check that the post get to the correct group page
        when the group is selected.
        """
        group_title = self.group.title
        page_url = self.project_page['group_posts']
        response = self.authorized_client.get(page_url)

        current_post_context = response.context['page'][0]
        expect_post_context = self.post
        current_group_context = response.context['group']
        expect_group_context = self.group

        self.assertEqual(
            current_post_context, expect_post_context,
            'Пост с выбранной группой не попадает на страницу группы.')
        self.assertEqual(
            current_group_context, expect_group_context,
            f'Группа на странице {page_url} указана неправильно. '
            f'Должна быть "{group_title}".')

    def test_new_page_show_correct_context(self):
        """Pages with form contain correct context."""
        form_pages = (
            self.project_page['new_post'],
            self.project_page['post_edit'],
        )
        form_fields = {
                'group': forms.fields.ChoiceField,
                'text': forms.fields.CharField,
                'image': forms.fields.ImageField,
            }
        for page_url in form_pages:
            response = self.authorized_client.get(page_url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields.get(value)
                    self.assertIsInstance(
                        form_field, expected,
                        f'Поле формы {value} на странице {page_url} '
                        f'не совпадает с заданным классом {expected}.')

    def test_group_page_do_not_include_post_with_another_group(self):
        """Post group match group of page."""
        another_group = Group.objects.create(
            title=('Еще одна тестовая группа'),
            slug='new-slug',
            description=('Еще одна тестовая группа')
        )
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': another_group.slug}))
        self.assertEqual(
            len(response.context['page'].object_list), 0,
            'Пост попал на страницу другой группы.')

    def test_cache_index_page_exist(self):
        """Index page cache exist and contain post list."""
        cache_page = self.project_page['index']
        response = self.authorized_client.get(cache_page)
        currect_context = response.context['page'][0]
        currect_cache = cache.get('index_page')[0]
        self.assertEqual(
            currect_context, currect_cache,
            f'Страница "{cache_page}" не кешируется.')

    def test_authorized_user_can_subscribe_and_unsubscribe_other_users(self):
        """Authorized user can subscribe and unsubscribe from another users."""
        follower = User.objects.create_user(username='Miniput')
        follower_client = Client()
        follower_client.force_login(follower)
        follow_page = self.project_page['profile_follow']
        unfollow_page = self.project_page['profile_unfollow']

        response = follower_client.get(follow_page) # noqa
        exist_connection = Follow.objects.filter(
            user=follower, author=self.author).exists()
        self.assertTrue(
            exist_connection,
            'Нельзя подписаться на автора, страница'
            f' "{follow_page}" работает некорректно.')

        response = follower_client.get(unfollow_page) # noqa
        not_exist_connection = Follow.objects.filter(
            user=follower, author=self.author).exists()
        self.assertFalse(
            not_exist_connection,
            'Нельзя отписаться от автора, страница'
            f' "{unfollow_page}" работает некорректно.')


class PaginatorViewsTest(TestCase):
    def setUp(self):
        User = get_user_model()
        author = User.objects.create_user(username='Artur')
        post_list = [Post(
            text=f'Тестовый пост {number}',
            author=author) for number in range(13)]
        Post.objects.bulk_create(post_list)
        self.client = Client()

    def test_paginator_correctly_deviding_posts(self):
        """First page contain 10 posts, second page contain 3 posts."""
        pages = {
            '': 10,
            '?page=2': 3,
        }
        for add_page_url, posts_per_page in pages.items():
            with self.subTest(value=add_page_url):
                response = self.client.get(
                    reverse('posts:index') + add_page_url)
                self.assertEqual(
                    len(response.context['page'].object_list),
                    posts_per_page,
                    'Паджинатор работает неправильно, на странице '
                    f'должно быть {posts_per_page} постов.')
