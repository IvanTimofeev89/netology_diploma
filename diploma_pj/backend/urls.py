from django.urls import path

from .views import CreateContact, RegisterUser

app_name = "backend"

urlpatterns = [
    path("user/register", RegisterUser.as_view(), name="user_register"),
    path("user/contact", CreateContact.as_view(), name="contact_create"),
]
