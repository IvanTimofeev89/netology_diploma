from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import Signal, receiver
from django_rest_passwordreset.signals import reset_password_token_created

from .models import ConfirmEmailToken, User

order_status_changed = Signal()


@receiver(post_save, sender=User)
def send_email_confirmation_token(sender, instance, created, **kwargs):
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


@receiver(reset_password_token_created)
def send_password_reset_token(sender, instance, reset_password_token, **kwargs):
    send_mail(
        # title:
        f"Token for password reset for {reset_password_token.user}",
        # message:
        f"Your password reset token is: {reset_password_token.key}",
        settings.DEFAULT_FROM_EMAIL,
        [reset_password_token.user.email],
        fail_silently=False,
    )


@receiver(order_status_changed)
def send_order_status_changed(user_id, **kwargs):
    user = User.objects.get(id=user_id)
    message = (
        f"Your order number {kwargs['data'].get('id')} status has "
        f"been changed to {kwargs['data'].get('status').capitalize()}"
    )

    send_mail(
        # title:
        "Your order status has been changed",
        # message:
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )