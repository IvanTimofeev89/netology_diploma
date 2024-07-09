from typing import Type

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ConfirmEmailToken, User


@receiver(post_save, sender=User)
def send_email_confirmation_token(sender: Type[User], instance: User, created: bool, **kwargs):
    if created and not instance.is_email_confirmed:
        # send an e-mail to the user
        token, _ = ConfirmEmailToken.objects.get_or_create(user_id=instance.pk)

        send_mail(
            "Email Confirmation",
            f"Your confirmation token is: {token.key}",
            settings.DEFAULT_FROM_EMAIL,
            [instance.email],
            fail_silently=False,
        )
