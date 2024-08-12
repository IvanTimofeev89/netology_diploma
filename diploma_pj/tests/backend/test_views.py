import pytest


from backend.models import User


@pytest.mark.django_db
def test_register_user(api_client):
    response = api_client.post('/api/v1/user/register/', {
        'email': 'test@example.com',
        'password': 'testpassword',
        'first_name': 'John',
        'last_name': 'Doe'
    })
    assert response.status_code == 201
    assert response.data['message'] == 'User created successfully'
    assert User.objects.filter(email='test@example.com').exists()

@pytest.mark.django_db
def test_register_user_missing_fields(api_client):
    response = api_client.post('/api/v1/user/register/', {
        'email': 'test@example.com'
    })
    assert response.status_code == 400
    assert 'Password is required' in response.data.get('non_field_errors')[0]


@pytest.mark.django_db
def test_login_user(api_client, user):
    response = api_client.post('/api/v1/user/login/', {
        'email': 'test@example.com',
        'password': 'testpassword'
    })
    assert response.status_code == 201
    assert 'token' in response.data

@pytest.mark.django_db
def test_login_invalid_user(api_client, user):
    response = api_client.post('/api/v1/user/login/', {
        'email': 'invalid@example.com',
        'password': 'invalidpassword'
    })
    assert response.status_code == 401