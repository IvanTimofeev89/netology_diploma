import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from dotenv import load_dotenv

User = get_user_model()

load_dotenv()


class Command(BaseCommand):
    help = "Command to crate superuser"

    def handle(self, *args, **kwargs):
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(email=email, password=password)
