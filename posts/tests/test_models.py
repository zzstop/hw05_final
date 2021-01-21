from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Comment, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    def setUp(self):
        test_author = User.objects.create_user(username='Artur')
        test_group = Group.objects.create(title='Тестовая группа')
        self.post = Post.objects.create(
            text='Я' * 20,
            author=test_author,
            group=test_group
        )

    def test_verbose_name(self):
        """verbose_name in fields is the same as expected."""
        post = self.post
        field_verboses = {
            'text': 'текст',
            'author': 'автор',
            'group': 'группа',
            'image': 'картинка'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected,
                    f'verbose_name поля {value} модели Post неверное.')

    def test_help_text(self):
        """help_text in fields is the same as expected."""
        post = self.post
        field_help_textes = {
            'text': 'Перед публикацией заполните поле.',
            'group': 'Выберите группу для публикации поста.',
            'image': 'Выберите картинку для публикации поста.',
        }
        for value, expected in field_help_textes.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected,
                    f'help_text поля {value} модели Post неверное.')

    def test_str_method(self):
        """"__str__ method match first 15 simbols of post.text."""
        post = self.post
        expected_show_object = 'Я' * 15
        self.assertEquals(
            expected_show_object, str(post),
            'Метод __str__ модели Post работает неправильно.')


class GroupModelTest(TestCase):
    def test_str_method(self):
        """"__str__ method match group.title."""
        test_group = Group.objects.create(title='Тестовая группа')
        expected_show_object = 'Тестовая группа'
        self.assertEquals(
            expected_show_object, str(test_group),
            'Метод __str__ модели Group работает неправильно.')


class CommentModelTest(TestCase):
    def test_str_method(self):
        """"__str__ method match first 15 simbols of comment.text."""
        test_author = User.objects.create_user(username='Artur')
        test_post = Post.objects.create(
            text='Тестовый пост',
            author=test_author,
        )
        test_comment = Comment.objects.create(
            post=test_post,
            author=test_author,
            text='Я' * 20
        )
        expected_show_object = 'Я' * 15
        self.assertEquals(
            expected_show_object, str(test_comment),
            'Метод __str__ модели Comment работает неправильно.')
