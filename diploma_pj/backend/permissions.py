from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission

User = get_user_model()


class EmailPasswordPermission(BasePermission):
    def has_permission(self, request, view):
        # email = request.headers.get('email')
        # password = request.headers.get('password')
        #
        # if email and password:
        #     try:
        #        user = User.objects.get(email=email)
        #     except User.DoesNotExist:
        #         return False
        # if user.check_password(password):
        #     return True
        # return False
        return True
