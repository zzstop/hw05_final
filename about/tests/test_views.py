from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.static_urls = {
            'author': reverse('about:author'),
            'tech': reverse('about:tech'),
        }

    def test_static_pages_exists_at_desired_location(self):
        """Static page available to any user."""
        for url in StaticViewsTests.static_urls.values():
            response = StaticViewsTests.guest_client.get(url)
            with self.subTest(value=url):
                self.assertEqual(
                    response.status_code, 200,
                    f'Страница по адресу {url} недоступна.')

    def test_static_pages_use_correct_template(self):
        """Static page use correct template."""
        templates_url_names = {
            'about/author.html': StaticViewsTests.static_urls['author'],
            'about/tech.html': StaticViewsTests.static_urls['tech'],
        }
        for template, url in templates_url_names.items():
            with self.subTest(value=template):
                response = StaticViewsTests.guest_client.get(url)
                self.assertTemplateUsed(
                    response, template,
                    f'Страница "{url}" использует неверный шаблон, '
                    f'требуется {template}')
