import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

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
        self.follower = User.objects.create_user(username='Miniput')
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
            'follow_index': reverse('posts:follow_index'),
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
            'add_comment': reverse('posts:add_comment', kwargs={
                'username': self.author.username, 'post_id': self.post.pk}),
        }
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)

    def test_pages_use_correct_template(self):
        """Pages use appropriate template."""
        templates_pages_names = {
            'index.html': (self.project_page['index'],),
            'group.html': (self.project_page['group_posts'],),
            'profile.html': (self.project_page['profile'],),
            'post.html': (self.project_page['post'],),
            'new_post.html': (
                self.project_page['new_post'],
                self.project_page['post_edit'],),
            'follow.html': (self.project_page['follow_index'],),
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

    def test_follow_page_show_correct_context_for_follower(self):
        """Follow page of subscriber contain new post from following author."""
        follow_page = self.project_page['follow_index']
        Follow.objects.create(
            user=self.follower, author=self.author)
        response = self.follower_client.get(follow_page)
        currect_context = response.context['page'][0]
        expected_context = self.post
        self.assertEqual(
            currect_context, expected_context,
            f'На страницу ленты подписчика "{follow_page}"'
            ' не выводится пост интересующего автора.')

    def test_follow_page_show_correct_context_for_unfollow_user(self):
        """
        Follow page of unsubscribed user don't contain
        new post from strange author.
        """
        follow_page = self.project_page['follow_index']
        response = self.follower_client.get(follow_page)
        current_context = response.context['page']
        self.assertEqual(
            len(current_context), 0,
            f'На страницу ленты подписчика "{follow_page}"'
            ' выводится пост автора, на которого пользователь не подписан.')

    def test_group_page_do_not_include_post_with_another_group(self):
        """Post group match group of page."""
        another_group = Group.objects.create(
            title='Еще одна тестовая группа',
            slug='new-slug',
            description='Еще одна тестовая группа'
        )
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': another_group.slug}))
        self.assertEqual(
            len(response.context['page'].object_list), 0,
            'Пост попал на страницу другой группы.')

    def test_cache_index_page_exist(self):
        """Index page cache exist."""
        cache_page = self.project_page['index']
        cache_content = self.authorized_client.get(cache_page).content
        Post.objects.create(
            text='Пост для проверки кеша',
            author=self.author)
        new_content = self.authorized_client.get(cache_page).content
        self.assertEqual(
            cache_content, new_content,
            f'Страница "{cache_page}" не кешируется.')

    def test_authorized_user_can_subscribe_other_users(self):
        """Authorized user can subscribe another users."""
        follow_page = self.project_page['profile_follow']
        self.follower_client.get(follow_page)
        exist_connection = Follow.objects.filter(
            user=self.follower, author=self.author).exists()
        self.assertTrue(
            exist_connection,
            'Нельзя подписаться на автора, страница'
            f' "{follow_page}" работает некорректно.')

    def test_authorized_user_can_unsubscribe_other_users(self):
        """Authorized user can unsubscribe from another users."""
        unfollow_page = self.project_page['profile_unfollow']
        Follow.objects.create(
            user=self.follower, author=self.author)
        self.follower_client.get(unfollow_page)
        not_exist_connection = Follow.objects.filter(
            user=self.follower, author=self.author).exists()
        self.assertFalse(
            not_exist_connection,
            'Нельзя отписаться от автора, страница'
            f' "{unfollow_page}" работает некорректно.')

    def test_anonymous_user_can_not_comment_post(self):
        """Anonymous user can't comment post."""
        comment_url = self.project_page['add_comment']
        guest_client = Client()
        guest_client.post(
            comment_url,
            {'text': 'Тестовый комментарий'},
            follow=True)
        comment = Comment.objects.filter(pk=1).exists()
        self.assertFalse(
            comment,
            'Неавторизованный пользователь смог оставить комментарий.')

    def test_authorized_user_can_comment_post(self):
        """Authorized user can comment post and redirect to the 'post' page."""
        comment_url = self.project_page['add_comment']
        post_url = self.project_page['post']
        response = self.authorized_client.post(
            comment_url,
            {'text': 'Тестовый комментарий'},
            follow=True)
        self.assertRedirects(response, post_url)
        comment = Comment.objects.filter(pk=1).exists()
        self.assertTrue(
            comment,
            'Авторизованный пользователь не может оставить комментарий.')


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
