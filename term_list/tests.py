from django.urls import reverse, resolve
from django.test import TestCase
from django.http import HttpRequest

from .views import begrepp_view

class OLLIPageTest(TestCase):

    def test_root_url_resolves_to_home_page_view(self):
        # find what function this url maps to
        found = resolve('/') #
        self.assertEqual(found.func, begrepp_view)

    def test_home_page_returns_correct_html(self):
        request = HttpRequest()
        response = home_page(request)
        self.assertTrue(response.content.startswith(b'<html>'))
        self.assertIn('<title>VGR Informatik - OLLI Begreppstjänst</title>', response.content)
        self.assertTrue(response.content.endswith(b'</html>'))