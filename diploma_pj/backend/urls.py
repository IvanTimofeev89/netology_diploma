from django.urls import path

from .views import (
    Login,
    ManageContact,
    ManageUserAccount,
    PartnerState,
    PartnerUpdate,
    RegisterUser,
)

app_name = "backend"

urlpatterns = [
    path("user/login/", Login.as_view(), name="login"),
    path("user/register/", RegisterUser.as_view(), name="user_register"),
    path("user/contact/", ManageContact.as_view(), name="contact_handling"),
    path("user/details/", ManageUserAccount.as_view(), name="user_handling"),
    path("partner/update/", PartnerUpdate.as_view(), name="partner_update"),
    path("partner/state/", PartnerState.as_view(), name="partner_state"),
]
