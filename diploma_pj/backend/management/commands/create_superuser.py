from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Command to crate superuser"

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, help="Superuser email")
        parser.add_argument("--password", type=str, help="Superuser password")

    def handle(self, *args, **kwargs):
        email = kwargs.get("email", "admin@example.com")
        password = kwargs.get("password", "admin")

        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(email=email, password=password)
