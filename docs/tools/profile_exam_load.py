"""Run the existing load command with optional connection and CPU counters."""
import argparse
import os
from pathlib import Path
import sys
from threading import Lock
from time import perf_counter, process_time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--conn-max-age', type=int,
                        help='Experiment with persistent database connections in this process only.')
    args, workload = parser.parse_known_args()
    sys.path.insert(0, str(args.project.resolve()))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Online_Exam_Portal.settings')
    import django
    if args.conn_max_age is not None:
        from django.conf import settings
        database = settings.DATABASES['default']
        if args.conn_max_age < 0 or database['ENGINE'] != 'django.db.backends.postgresql':
            parser.error('--conn-max-age requires a nonnegative value and PostgreSQL')
        database.update(CONN_MAX_AGE=args.conn_max_age, CONN_HEALTH_CHECKS=bool(args.conn_max_age))
    django.setup()
    from django.core.management import call_command
    from django.db.backends.signals import connection_created
    from exams.management.commands.measure_load import Command

    class InstrumentedLoad(Command):
        def _run(self, *args, **kwargs):
            opened = 0
            counter_lock = Lock()

            def observe(sender, **kwargs):
                nonlocal opened
                with counter_lock:
                    opened += 1

            connection_created.connect(observe, weak=False)
            wall = perf_counter()
            cpu = process_time()
            try:
                result = super()._run(*args, **kwargs)
            finally:
                connection_created.disconnect(observe)
            result['profile'] = dict(connections_opened=opened, cpu_seconds=process_time()-cpu,
                                     elapsed_seconds=perf_counter()-wall)
            return result

        @staticmethod
        def _evaluate(baseline, loaded, users_n):
            result = Command._evaluate(baseline, loaded, users_n)
            result['profile'] = {'single': baseline['profile'], 'concurrent': loaded['profile']}
            return result

    call_command(InstrumentedLoad(), *workload)


if __name__ == '__main__':
    main()
