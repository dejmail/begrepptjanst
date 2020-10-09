from django.urls import resolve
from django.test import TestCase
from django.http import HttpRequest
from .views import begrepp_view

class HomePageTest(TestCase):
    def test_root_url_resolves_to_home_page_view(self):
        found = resolve('/')
        self.assertEqual(found.func, begrepp_view)
    
    def test_home_page_returns_correct_html(self):
        request = HttpRequest()
        response = begrepp_view(request)
        self.assertTrue(response.content.startswith(b'<!doctype html>'))
        self.assertIn('<title>VGR Informatik - OLLI Begreppstjänst</title>', response.content)
        self.assertTrue(response.content.endswith('</html>'))