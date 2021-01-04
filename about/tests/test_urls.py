from django.test import Client, TestCase


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.static_urls = {
            'author': '/about/author/',
            'tech': '/about/tech/',
        }

    def test_static_urls_exists_at_desired_location(self):
        """Static url available to any user."""
        for url in StaticURLTests.static_urls.values():
            response = StaticURLTests.guest_client.get(url)
            with self.subTest(value=url):
                self.assertEqual(
                    response.status_code, 200,
                    f'Адрес {url} недоступен.')

    def test_static_urls_use_correct_template(self):
        """Static url use correct template."""
        templates_url_names = {
            'about/author.html': StaticURLTests.static_urls['author'],
            'about/tech.html': StaticURLTests.static_urls['tech'],
        }
        for template, url in templates_url_names.items():
            with self.subTest(value=template):
                response = StaticURLTests.guest_client.get(url)
                self.assertTemplateUsed(
                    response, template,
                    f'Адрес "{url}" использует неверный шаблон, '
                    f'требуется {template}')
