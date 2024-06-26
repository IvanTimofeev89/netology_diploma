from django.urls import path

from .views import RegisterUser

app_name = "backend"

urlpatterns = [
    path("user/register", RegisterUser.as_view(), name="user_register"),
]
