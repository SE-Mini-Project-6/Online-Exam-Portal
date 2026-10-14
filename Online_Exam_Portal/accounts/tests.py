"""
Authentication tests for the Online Exam Portal.
Tests cover login functionality, password security, and role-aware sessions.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login
from django.urls import reverse

User = get_user_model()


class AuthenticationTests(TestCase):
    """Test suite for authentication and login functionality."""

    def setUp(self):
        """Set up test users - admin and student."""
        # Create admin user with staff privileges
        self.admin_user = User.objects.create_staff_user(
            username='admin',
            email='admin@examportal.com',
            password='AdminPass123!'
        )
        # Create regular student user
        self.student_user = User.objects.create_user(
            username='student',
            email='student@examportal.com',
            password='StudentPass123!'
        )
        # Create another student for testing
        self.another_student = User.objects.create_user(
            username='student2',
            email='student2@examportal.com',
            password='StudentPass123!'
        )

        self.factory = RequestFactory()

    def test_admin_user_creation(self):
        """Test that admin user is created with is_staff=True."""
        self.assertTrue(self.admin_user.is_staff)
        self.assertTrue(self.admin_user.is_superuser)

    def test_student_user_creation(self):
        """Test that regular student user is created with is_staff=False."""
        self.assertFalse(self.student_user.is_staff)
        self.assertFalse(self.student_user.is_superuser)

    def test_admin_login_valid(self):
        """Test admin signs in with valid credentials."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'admin',
            'password': 'AdminPass123!'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful login
        self.assertTrue(self.client.session.session_key)

    def test_admin_login_invalid(self):
        """Test admin login rejected with invalid credentials."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'admin',
            'password': 'WrongPassword123!'
        })
        self.assertEqual(response.status_code, 200)  # Re-render login form
        # Generic error message to prevent username enumeration
        self.assertContains(response, 'Invalid username or password.')

    def test_student_login_valid(self):
        """Test student signs in with valid credentials."""
        response = self.client.post(reverse('accounts:student-login'), {
            'username': 'student',
            'password': 'StudentPass123!'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful login
        self.assertTrue(self.client.session.session_key)

    def test_student_login_invalid(self):
        """Test student login rejected with invalid credentials."""
        response = self.client.post(reverse('accounts:student-login'), {
            'username': 'student',
            'password': 'WrongPassword123!'
        })
        self.assertEqual(response.status_code, 200)  # Re-render login form
        self.assertContains(response, 'Invalid username or password.')

    def test_password_hashing_security(self):
        """Test that passwords are stored with salted hash (not plain text)."""
        # Check that password field is not the raw password
        self.assertNotEqual(self.admin_user.password, 'AdminPass123!')
        self.assertNotEqual(self.student_user.password, 'StudentPass123!')

        # Verify check_password works correctly
        self.assertTrue(self.admin_user.check_password('AdminPass123!'))
        self.assertTrue(self.student_user.check_password('StudentPass123!'))

        # Verify check_password rejects wrong passwords
        self.assertFalse(self.admin_user.check_password('WrongPassword'))
        self.assertFalse(self.student_user.check_password('WrongPassword'))

    def test_role_aware_session_redirect(self):
        """Test role-aware session redirect after login."""
        # Login as admin
        self.client.post(reverse('accounts:login'), {
            'username': 'admin',
            'password': 'AdminPass123!'
        })

        # Admin should be redirected to admin dashboard
        # and have is_staff=True in session context
        self.assertTrue(self.client.user.is_staff)
        self.assertTrue(self.client.user.is_authenticated)

        # Login as student
        self.client.post(reverse('accounts:student-login'), {
            'username': 'student',
            'password': 'StudentPass123!'
        })

        # Student should NOT have staff privileges
        self.assertFalse(self.client.user.is_staff)
        self.assertTrue(self.client.user.is_authenticated)

    def test_session_persistence(self):
        """Test that session persists across requests."""
        # Login as admin
        login_response = self.client.post(reverse('accounts:login'), {
            'username': 'admin',
            'password': 'AdminPass123!'
        })

        # Make another request - session should persist
        authenticated_response = self.client.get(reverse('accounts:admin_dashboard'))

        # User should still be authenticated
        self.assertEqual(authenticated_response.status_code, 200)
        self.assertTrue(self.client.user.is_staff)

    def test_csrf_protection(self):
        """Test that CSRF protection is in place for login."""
        # GET request should serve the login form with CSRF token
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'csrf')

    def test_multiple_failed_login_attempts(self):
        """Test that multiple failed login attempts are handled."""
        # Try multiple invalid login attempts
        for _ in range(3):
            response = self.client.post(reverse('accounts:login'), {
                'username': 'admin',
                'password': 'WrongPassword'
            })
            self.assertEqual(response.status_code, 200)

        # User should still not be logged in
        self.assertFalse(self.client.user.is_authenticated)

    def test_admin_and_student_can_both_login(self):
        """Test that both admin and student can login successfully."""
        # Admin login
        admin_response = self.client.post(reverse('accounts:login'), {
            'username': 'admin',
            'password': 'AdminPass123!'
        })
        self.assertTrue(admin_response.wsgi_request.user.is_staff)

        # Logout
        from django.contrib.auth import logout
        logout(admin_response.wsgi_request)

        # Student login
        student_response = self.client.post(reverse('accounts:student-login'), {
            'username': 'student',
            'password': 'StudentPass123!'
        })
        self.assertTrue(student_response.wsgi_request.user.is_authenticated)
        self.assertFalse(student_response.wsgi_request.user.is_staff)