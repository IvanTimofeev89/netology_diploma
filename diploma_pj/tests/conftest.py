import pytest
from backend.models import Order, User
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def confirmed_email_user(db):
    return User.objects.create_user(
        email="test@example.com", password="testpassword", is_email_confirmed=True
    )


@pytest.fixture
def user(db):
    return User.objects.create_user(email="test@example.com", password="testpassword")


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(email="admin@example.com", password="testpassword")


@pytest.fixture
def basket(confirmed_email_user):
    return Order.objects.create(user=confirmed_email_user, status="basket")


@pytest.fixture
def order(confirmed_email_user):
    return Order.objects.create(user=confirmed_email_user, status="confirmed")
