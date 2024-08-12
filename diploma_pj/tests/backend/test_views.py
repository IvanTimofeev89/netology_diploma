import pytest
from backend.models import Order, User

"""
Tests for user registration
"""


@pytest.mark.django_db
def test_register_user(api_client):
    """
    Test the user registration endpoint with valid data.

    Asserts that a user is successfully created and the correct response is returned.
    """
    response = api_client.post(
        "/api/v1/user/register/",
        {
            "email": "test@example.com",
            "password": "testpassword",
            "first_name": "John",
            "last_name": "Doe",
        },
    )
    assert response.status_code == 201
    assert response.data["message"] == "User created successfully"
    assert User.objects.filter(email="test@example.com").exists()


@pytest.mark.django_db
def test_register_user_missing_fields(api_client):
    """
    Test the user registration endpoint with missing required fields.

    Asserts that the response indicates a validation error for missing fields.
    """
    response = api_client.post("/api/v1/user/register/", {"email": "test@example.com"})
    assert response.status_code == 400
    assert "Password is required" in response.data.get("non_field_errors")[0]


"""
Tests for user login
"""


@pytest.mark.django_db
def test_login_user(api_client, user):
    """
    Test the user login endpoint with valid credentials.

    Asserts that a login attempt returns a success status and a token.
    """
    response = api_client.post(
        "/api/v1/user/login/", headers={"email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 201
    assert "token" in response.data


@pytest.mark.django_db
def test_login_invalid_user(api_client, user):
    """
    Test the user login endpoint with invalid credentials.

    Asserts that a login attempt with incorrect credentials returns an error status.
    """
    response = api_client.post(
        "/api/v1/user/login/",
        headers={"email": "invalid@example.com", "password": "invalidpassword"},
    )
    assert response.status_code == 401


"""
Tests for user managing
"""


@pytest.mark.django_db
def test_get_user_account(api_client, user):
    """
    Test retrieving the user account information.

    Asserts that the correct user information is returned when authenticated.
    """
    response = api_client.get(
        "/api/v1/user/details/", headers={"email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert response.data["email"] == user.email


@pytest.mark.django_db
def test_update_user_account(api_client, user):
    """
    Test updating the user account information.

    Asserts that the user information is successfully updated.
    """
    response = api_client.patch(
        "/api/v1/user/details/",
        headers={"email": "test@example.com", "password": "testpassword"},
        data={"first_name": "NewName"},
    )
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.first_name == "NewName"


"""
Tests for order managing
"""


@pytest.mark.django_db
def test_create_order(api_client, confirmed_email_user, admin_user, basket):
    """
    Test creating an order with a basket status.

    Asserts that an order is successfully created for the authenticated user.
    """
    response = api_client.post(
        "/api/v1/orders/", headers={"email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 201
    assert Order.objects.filter(user=confirmed_email_user, status="placed").exists()


@pytest.mark.django_db
def test_get_orders(api_client, confirmed_email_user, order):
    """
    Test retrieving the list of orders.

    Asserts that a list of orders is returned and contains at least one order.
    """
    response = api_client.get(
        "/api/v1/orders/", headers={"email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert len(response.data) > 0
