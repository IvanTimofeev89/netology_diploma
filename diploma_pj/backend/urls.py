from django.urls import path

from .views import LoginView, ManageContact, ManageUserAccount, RegisterUser

app_name = "backend"

urlpatterns = [
    path("user/login/", LoginView.as_view(), name="login"),
    path("user/register/", RegisterUser.as_view(), name="user_register"),
    path("user/contact/", ManageContact.as_view(), name="contact_handling"),
    path("user/details/", ManageUserAccount.as_view(), name="user_handling"),
]
