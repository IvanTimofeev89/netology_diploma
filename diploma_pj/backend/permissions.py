from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission, IsAuthenticated

User = get_user_model()


class EmailPasswordPermission(BasePermission):
    def has_permission(self, request, view):
        email = request.headers.get("email")
        password = request.headers.get("password")

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return False
            if user.check_password(password):
                request.user = user
                return True
        return False


class EmailOrTokenPermission(BasePermission):
    def has_permission(self, request, view):
        return EmailPasswordPermission() or IsAuthenticated()


# class IsOwnerOrAdminPermission(BasePermission):
#     def has_permission(self, request, view):
#         return EmailPasswordPermission() or IsAdminUser()
