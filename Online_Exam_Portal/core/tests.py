"""
Core tests for the Online Exam Portal.
Tests cover homepage and role selection functionality.
"""
from django.test import TestCase, SimpleTestCase, override_settings
from django.urls import reverse, resolve


@override_settings(SECURE_SSL_REDIRECT=False)  # plain-HTTP test client; HTTPS is covered in accounts/test_security.py
class HomeTests(SimpleTestCase):
    """Test suite for homepage and role selection."""

    def test_home_url_resolves(self):
        """Test that home URL resolves correctly."""
        url = reverse('core:home')
        self.assertEqual(url, '/')

    def test_homepage_contains_login_links(self):
        """Test that homepage contains links to both login types."""
        from django.test.client import Client
        client = Client()
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        # Check for admin login link
        self.assertContains(response, 'Admin Login')
        # Check for student login link
        self.assertContains(response, 'Student Login')


@override_settings(SECURE_SSL_REDIRECT=False)
class URLConfigurationTests(TestCase):
    """Test URL configuration is correct."""

    def test_accounts_urls_configured(self):
        """Test that accounts app URLs are properly configured."""
        from django.urls import resolve
        # Test login URL
        login_url = reverse('accounts:login')
        self.assertIsNotNone(login_url)

        # Test student login URL
        student_login_url = reverse('accounts:student-login')
        self.assertIsNotNone(student_login_url)

        # Test logout URL
        logout_url = reverse('accounts:logout')
        self.assertIsNotNone(logout_url)