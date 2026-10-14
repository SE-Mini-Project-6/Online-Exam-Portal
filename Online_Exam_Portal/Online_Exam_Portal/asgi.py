import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Online_Exam_Portal.settings")

application = get_asgi_application()