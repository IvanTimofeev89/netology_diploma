from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission

User = get_user_model()


class EmailPasswordPermission(BasePermission):
    def has_permission(self, request, view):
        #        email = request.headers.get('email')
        #        password = request.headers.get('password')

        #        if not email or not password:
        #            return False

        #        try:
        #            user = User.objects.get(email=email)
        #        except User.DoesNotExist:
        #            return False

        #        if user.check_password(password):
        #            request.user = user
        #            return True
        return True
