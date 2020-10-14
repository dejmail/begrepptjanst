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
        self.assertTrue(response.content.startswith(b'\n'))
        self.assertIn(b'<title style="font-family: frutiger;">VGR Informatik - OLLI Begreppstj\xc3\xa4nst</title>', response.content)
        self.assertTrue(response.content.endswith(b'\n'))
        self.assertIn(b'function whatDoYouWant(requested_term)', msg='cannot find this function in the HTML', container=response.content)
        self.assertIn(b'function populate_request_form(requested_term)', msg='cannot find this function in the HTML', container=response.content)
        self.assertIn(b'function scrollToHelp()', msg='cannot find this function in the HTML', container=response.content)
        self.assertIn(b'function clear_mittenspanrow()', msg='cannot find this function in the HTML', container=response.content)
        
