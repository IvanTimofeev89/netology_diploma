# from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .serializers import UserSerializer


# Create your views here.
class RegisterUser(APIView):
    """
    Class for user registration.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse({"message": "User created successfully"})
