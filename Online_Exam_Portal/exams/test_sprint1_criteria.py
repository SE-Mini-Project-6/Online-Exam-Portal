from datetime import timedelta
from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Exam


class InputValuesParser(HTMLParser):
    """Keep the rendered admin form fields, including inline form fields."""

    def __init__(self):
        super().__init__()
        self.values = {}

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            fields = dict(attrs)
            name = fields.get("name")
            if name:
                self.values[name] = fields.get("value", "")


@override_settings(SECURE_SSL_REDIRECT=False)
class ExamAdminCrudTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_superuser(
            username="exam-crud-admin",
            email="exam-crud-admin@example.com",
            password="AdminPass123!",
        )

        start_at = timezone.now() + timedelta(days=1)
        self.exam = Exam.objects.create(
            title="Original exam",
            duration_minutes=60,
            start_at=start_at,
            end_at=start_at + timedelta(hours=2),
        )
        self.client.force_login(self.admin)

    def test_admin_can_update_exam(self):
        url = reverse("admin:exams_exam_change", args=[self.exam.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        parser = InputValuesParser()
        parser.feed(response.content.decode())
        form_data = parser.values
        form_data.update({
            "title": "Updated exam",
            "duration_minutes": "45",
            "start_at_0": self.exam.start_at.strftime("%Y-%m-%d"),
            "start_at_1": self.exam.start_at.strftime("%H:%M:%S"),
            "end_at_0": self.exam.end_at.strftime("%Y-%m-%d"),
            "end_at_1": self.exam.end_at.strftime("%H:%M:%S"),
            "_save": "Save",
        })

        response = self.client.post(url, form_data)

        self.assertEqual(response.status_code, 302)
        self.exam.refresh_from_db()
        self.assertEqual(self.exam.title, "Updated exam")
        self.assertEqual(self.exam.duration_minutes, 45)

    def test_admin_can_delete_exam(self):
        url = reverse("admin:exams_exam_delete", args=[self.exam.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, {"post": "yes"})

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Exam.objects.filter(pk=self.exam.pk).exists())