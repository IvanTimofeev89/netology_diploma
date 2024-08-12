from django.urls import include, path

from .views import (
    CategoryList,
    EmailConfirm,
    Login,
    ManageBasket,
    ManageContact,
    ManageOrder,
    ManageUserAccount,
    PartnerState,
    PartnerUpdate,
    ProductsList,
    RegisterUser,
    ShopList,
)

app_name = "backend"

urlpatterns = [
    path("user/login/", Login.as_view(), name="login"),
    path("user/register/", RegisterUser.as_view(), name="user_register"),
    path("user/register/confirm/", EmailConfirm.as_view(), name="email_confirm"),
    path("password_reset/", include("django_rest_passwordreset.urls", namespace="password_reset")),
    path("user/contact/", ManageContact.as_view(), name="contact_handling"),
    path("user/details/", ManageUserAccount.as_view(), name="user_handling"),
    path("partner/update/", PartnerUpdate.as_view(), name="partner_update"),
    path("partner/state/", PartnerState.as_view(), name="partner_state"),
    path("shops/", ShopList.as_view(), name="shop_list"),
    path("categories/", CategoryList.as_view(), name="shop_list"),
    path("orders/", ManageOrder.as_view(), name="order_handling"),
    path("products/", ProductsList.as_view(), name="products_list"),
    path("basket/", ManageBasket.as_view(), name="basket_handling"),
]
