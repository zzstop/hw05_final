import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

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
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post_without_group(self):
        """
        Valid form create a new post without group
        and redirect to the 'index' page.
        """
        page_url = reverse('posts:new_post')
        post_count = Post.objects.count()
        response = self.authorized_client.post(
            page_url,
            {'text': 'Пост без группы'},
            follow=True)
        post = Post.objects.get(pk=1)
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(
            Post.objects.count(), post_count+1,
            f'Форма на странице {page_url} не сохраняет'
            ' запись без выбранной группы.')
        self.assertEqual(
            post.text, 'Пост без группы',
            'Созданный без группы пост сохраняется с неправильными данными.')

    def test_create_post_with_group(self):
        """
        Valid form create a new post with group
        and redirect to the 'index' page.
        """
        page_url = reverse('posts:new_post')
        post_count = Post.objects.count()
        response = self.authorized_client.post(
            page_url,
            {'text': 'Пост c группой', 'group': self.group.id},
            follow=True)
        post = Post.objects.get(pk=1)
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(
            Post.objects.count(), post_count+1,
            f'Форма на странице {page_url} не сохраняет'
            ' запись с выбранной группой.')
        self.assertEqual(
            post.text, 'Пост c группой',
            'Созданный с группой пост сохраняется с неправильными данными.')

    def test_create_post_with_image(self):
        """
        Valid form create a new post with image
        and redirect to the 'index' page.
        """
        page_url = reverse('posts:new_post')
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        response = self.authorized_client.post(
            page_url,
            {'text': 'Пост c группой', 'image': uploaded},
            follow=True)
        post = Post.objects.get(pk=1)
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(
            Post.objects.count(), post_count+1,
            f'Форма на странице {page_url} не сохраняет'
            ' запись с загруженной картинкой.')
        self.assertEqual(
            post.text, 'Пост c группой',
            'Созданный с картинкой пост сохраняется с неправильными данными.')

    def test_create_post_with_uncorrect_image(self):
        """
        New post form don't create a new post with
        uncorrect image, raise error.
        """
        not_image = SimpleUploadedFile(
            name='not_image',
            content=b'file')
        page_url = reverse('posts:new_post')
        response = self.authorized_client.post(
            page_url,
            {'text': 'Пост с неправильной картинкой', 'image': not_image})
        self.assertFormError(
            response, 'form', 'image',
            'Загрузите правильное изображение. Файл, который вы загрузили,'
            ' поврежден или не является изображением.')

    def test_edit_post(self):
        """Form change existing post and redirect to the 'post' page."""
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.author,
            group=self.group
        )
        post_url = reverse('posts:post', kwargs={
            'username': self.author.username, 'post_id': post.pk})
        edit_url = reverse('posts:post_edit', kwargs={
            'username': self.author.username, 'post_id': post.pk})
        response = self.authorized_client.post(
            edit_url,
            {'text': 'Обновленный тестовый текст'},
            follow=True
        )
        post = Post.objects.get(pk=post.pk)
        self.assertRedirects(response, post_url)
        self.assertNotEqual(
            post.text, 'Тестовый текст',
            f'Форма на странице {edit_url} не изменяет запись.')
