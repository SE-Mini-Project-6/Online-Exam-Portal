"""Finalize abandoned attempts whose server-side timer has expired."""
from django.core.management.base import BaseCommand
from django.utils import timezone

from exams.models import Attempt
from exams.timing import sync_attempt


class Command(BaseCommand):
    help = 'Finalize timed-out attempts (run periodically in a deployed scheduler).'

    def handle(self, *args, **options):
        now = timezone.now()
        expired = (Attempt.objects.filter(status=Attempt.IN_PROGRESS, deadline_at__lte=now)
                   .values_list('pk', flat=True))
        finalized = 0
        for pk in expired.iterator():
            _, changed = sync_attempt(pk, now=now)
            finalized += int(changed)
        self.stdout.write(f'Finalized {finalized} expired attempt(s).')
