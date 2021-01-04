from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    def setUp(self):
        self.post_author = User.objects.create_user(username='Artur')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.post_author,
            group=self.group
        )
        self.project_page = {
            'index': '/',
            'group_posts': '/group/test-slug/',
            'new_post': '/new/',
            'profile': '/Artur/',
            'post': '/Artur/1/',
            'post_edit': '/Artur/1/edit/',
        }
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post_author)

    def test_public_urls_exists_at_desired_location(self):
        """Public url-address available to any user."""
        public_url_names = (
            self.project_page['index'],
            self.project_page['group_posts'],
            self.project_page['profile'],
            self.project_page['post'],
        )
        for url in public_url_names:
            response = self.guest_client.get(url)
            with self.subTest(value=url):
                self.assertEqual(
                    response.status_code, 200,
                    f'Страница по адресу {url} недоступна для гостя.')

    def test_error_type_of_nonexistent_url(self):
        """Nonexistent URL return 'page not found' (404) error."""
        nonexistent_url = '/group/nonexistent_group/'
        response = self.guest_client.get(nonexistent_url)
        self.assertEqual(
            response.status_code, 404,
            'Несуществующая страница не возвращает ошибку 404.')

    def test_url_use_correct_template(self):
        """URL-address use correct template."""
        templates_url_names = {
            'index.html': (self.project_page['index'],),
            'group.html': (self.project_page['group_posts'],),
            'profile.html': (self.project_page['profile'],),
            'post.html': (self.project_page['post'],),
            'new_post.html': (
                self.project_page['new_post'],
                self.project_page['post_edit'],)
        }
        for template, url in templates_url_names.items():
            for url_name in url:
                with self.subTest(value=template):
                    response = self.authorized_client.get(url_name)
                    self.assertTemplateUsed(
                        response, template,
                        f'Адрес "{url_name}" использует неверный'
                        f' шаблон, требуется {template}')

    def test_close_urls_exists_and_redirect_anonymous_on_login(self):
        """
        Edit urls unavailable to unauthorized user
        and redirect to login.
        """
        edit_pages = {
            '/auth/login/?next=/new/':
                self.project_page['new_post'],
        }
        for redirect_page, page in edit_pages.items():
            with self.subTest(value=page):
                response = self.guest_client.get(page, follow=True)
                self.assertRedirects(response, redirect_page)

    def test_new_url_exists_at_desired_location_authorized(self):
        """URL 'new_post' available only to authorized user."""
        response = self.authorized_client.get(
            self.project_page['new_post'])
        self.assertEqual(
            response.status_code, 200,
            'Url /new/ недоступен '
            'для авторизованного пользователя.')

    def test_edit_post_url_exists_authorized_post_author(self):
        """
        Url 'post_edit' available to
        authorized author of this post.
        """
        response = self.authorized_client.get(
            self.project_page['post_edit'])
        self.assertEqual(
            response.status_code, 200,
            'Адрес /Artur/1/edit// недоступен '
            'для авторизованного автора поста.')

    def test_edit_post_url_exists_authorized_post_author1(self):
        """
        Url 'post_edit' unavailable to authorized user,
        which is different from the author of this post,
        and redirect to 'post' url.
        """
        another_user = User.objects.create_user(username='Miniput')
        authorised_not_post_client = Client()
        authorised_not_post_client.force_login(another_user)
        redirect_page = self.project_page['post']
        response = authorised_not_post_client.get(
            self.project_page['post_edit'])
        self.assertRedirects(response, redirect_page)
