from django.urls import path

from .views import LoginView, ManageContact, RegisterUser

app_name = "backend"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("user/register", RegisterUser.as_view(), name="user_register"),
    path("user/contact", ManageContact.as_view(), name="contact_create"),
]
