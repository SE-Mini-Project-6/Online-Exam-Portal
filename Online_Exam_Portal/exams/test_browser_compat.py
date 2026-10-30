from django.test import TestCase
from django.urls import reverse


class BrowserCompatibilityMarkupTests(TestCase):
    """NFR-07: markup basics that keep Chrome and Firefox consoles clean and layouts responsive."""

    def test_pages_declare_icon_viewport_and_language(self):
        # Chrome logged a SEVERE console error for the missing /favicon.ico on every page.
        response = self.client.get(reverse('accounts:student_login'), secure=True)
        self.assertContains(response, '<link rel="icon" href="data:image/svg+xml')
        self.assertContains(response, 'name="viewport" content="width=device-width, initial-scale=1.0"')
        self.assertContains(response, '<html lang="en">')
        self.assertContains(response, '<meta charset="UTF-8">')
