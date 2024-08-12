import pytest
from backend.models import User, Order
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()
@pytest.fixture
def user(db):
    return User.objects.create_user(email='test@example.com', password='testpassword')

@pytest.fixture
def basket(user):
    return Order.objects.create(user=user, status='basket')