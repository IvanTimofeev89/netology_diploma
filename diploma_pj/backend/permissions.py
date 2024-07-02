from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission, IsAuthenticated

User = get_user_model()

#
# class EmailPasswordPermission(BasePermission):
#     def has_permission(self, request, view):
#         email = request.headers.get("email")
#         password = request.headers.get("password")
#
#         if email and password:
#             try:
#                 user = User.objects.get(email=email)
#             except User.DoesNotExist:
#                 return False
#             if user.check_password(password):
#                 request.user = user
#                 return user
#         raise NeedLogin()
#
#
# class IsAuthenticated(BasePermission):
#     """
#     Allows access only to authenticated users.
#     """
#
#     def has_permission(self, request, view):
#         if bool(request.user and request.user.is_authenticated):
#             return request.user
#         raise NeedLogin()
#
#
# class EmailOrTokenPermission(BasePermission):
#     def has_permission(self, request, view):
#         user = EmailPasswordPermission().has_permission(request, view)
#         if user:
#             request.user = user
#             return user
#         return IsAuthenticated().has_permission(request, view)

class EmailPasswordPermission(BasePermission):
    def has_permission(self, request, view):
        email = request.headers.get("email")
        password = request.headers.get("password")
        token = request.headers.get("Authorization")

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return False
            if user.check_password(password):
                request.user = user
                return user
        if token:
            return None
        raise EmailPassExc()

class EmailOrTokenPermission(BasePermission):
    def has_permission(self, request, view):
        user = EmailPasswordPermission().has_permission(request, view)
        if user:
            request.user = user
            return True
        return IsAuthenticated().has_permission(request, view)


class OnlyShopPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.type == "shop":
            return True
        raise OnlyShop()


class EmailPassExc(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = {
        "detail": "Email or password were incorrect or not provided.",
    }
    default_code = "not_authenticated"

class OnlyShop(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = {
        "detail": "Only for Shops"
    }
    default_code = "not_authenticated"
