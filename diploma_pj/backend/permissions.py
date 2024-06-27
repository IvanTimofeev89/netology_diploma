from django.contrib.auth import authenticate
from rest_framework.permissions import BasePermission


class LoginPasswordPermission(BasePermission):
    def has_permission(self, request, view):
        email = request.headers.get("email")
        password = request.headers.get("password")
        return authenticate(email=email, password=password)
