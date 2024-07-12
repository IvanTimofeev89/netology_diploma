from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import Signal, receiver
from django_rest_passwordreset.signals import reset_password_token_created

from .models import ConfirmEmailToken, Order, User

# Define a custom signal for order status changes
order_status_changed = Signal()


@receiver(post_save, sender=User)
def send_email_confirmation_token(sender: Any, instance: User, created: bool, **kwargs: Any):
    """
    Signal receiver to send an email confirmation token when a new user is created.

    Args:
        sender (Any): The model class that sent the signal.
        instance (User): The instance of the user created.
        created (bool): Boolean indicating whether a new record was created.
        **kwargs (Any): Additional keyword arguments.
    """
    if created and not instance.is_email_confirmed:
        # Create a confirmation token for the new user
        token, _ = ConfirmEmailToken.objects.get_or_create(user_id=instance.pk)

        # Send an email with the confirmation token
        send_mail(
            "Email Confirmation",
            f"Your confirmation token is: {token.key}",
            settings.DEFAULT_FROM_EMAIL,
            [instance.email],
            fail_silently=False,
        )


@receiver(reset_password_token_created)
def send_password_reset_token(sender: Any, instance: Any, reset_password_token: Any, **kwargs: Any):
    """
    Signal receiver to send a password reset token when the reset password token is created.

    Args:
        sender (Any): The model class that sent the signal.
        instance (Any): The instance of the signal sender.
        reset_password_token (Any): The token instance created for password reset.
        **kwargs (Any): Additional keyword arguments.
    """
    send_mail(
        # Title:
        f"Token for password reset for {reset_password_token.user}",
        # Message:
        f"Your password reset token is: {reset_password_token.key}",
        settings.DEFAULT_FROM_EMAIL,
        [reset_password_token.user.email],
        fail_silently=False,
    )


@receiver(order_status_changed)
def send_order_status_changed(user_id: int, **kwargs: Any):
    # """
    # Signal receiver to notify the user when the status of their order changes.
    #
    # Args:
    #     user_id (int): The ID of the user.
    #     **kwargs (Any): Additional keyword arguments, including order details.
    # """
    # user = User.objects.get(id=user_id)
    # message = (
    #     f"Status of your order with number {kwargs['data'].get('id')} has "
    #     f"been changed to '{kwargs['data'].get('status').capitalize()}'"
    # )
    #
    # # Send an email with the order status change notification
    # send_mail(
    #     # Title:
    #     "Your order status has been changed",
    #     # Message:
    #     message,
    #     settings.DEFAULT_FROM_EMAIL,
    #     [user.email],
    #     fail_silently=False,
    # )
    pass


@receiver(post_save, sender=Order)
def update_product_quantity(sender, instance, created, **kwargs):
    if instance.status == "confirmed" and not created:
        with transaction.atomic():
            order_items = instance.order_items.all()
            for item in order_items:
                product_info = item.product_info
                product_info.quantity -= item.quantity
                product_info.save()
