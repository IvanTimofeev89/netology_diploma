from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission, IsAuthenticated

from .models import User


class EmailOrTokenPermission(BasePermission):
    """
    Custom permission to allow access based on email
    and password authentication or token authentication.

    Methods:
        has_permission: Checks if the request has the necessary permissions.
    """

    def has_permission(self, request, view):
        """
        Check if the request has permission.

        Args:
            request: The HTTP request object.
            view: The view object.

        Returns:
            bool: True if permission is granted, False otherwise.

        Raises:
            EmailTokenPassExc: If email and password or Token were incorrect or not provided.
        """
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
                return True
        elif token:
            if IsAuthenticated().has_permission(request, view):
                token_user = request.user
                request.user = token_user
                return True

        raise EmailTokenPassExc()


class OnlyShopPermission(BasePermission):
    """
    Custom permission to allow access only to users of type 'shop'.

    Methods:
        has_permission: Checks if the request has the necessary permissions.
    """

    def has_permission(self, request, view):
        """
        Check if the request has permission.

        Args:
            request: The HTTP request object.
            view: The view object.

        Returns:
            bool: True if permission is granted, False otherwise.

        Raises:
            OnlyShop: If the user is not of type 'shop'.
        """
        user = request.user
        if user.type == "shop":
            return True
        raise OnlyShop()


class EmailTokenPassExc(APIException):
    """
    Custom exception for email/password or Token authentication failures.

    Attributes:
        status_code: HTTP status code for the exception.
        default_detail: Default detail message for the exception.
        default_code: Default code for the exception.
    """

    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = {
        "error": "Email and password or Token were incorrect or not provided.",
    }
    default_code = "not_authenticated"


class OnlyShop(APIException):
    """
    Custom exception for users who are not of type 'shop'.

    Attributes:
        status_code: HTTP status code for the exception.
        default_detail: Default detail message for the exception.
        default_code: Default code for the exception.
    """

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = {"error": "Only for Shops"}
    default_code = "not_authenticated"
