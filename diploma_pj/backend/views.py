# from django.shortcuts import render
from rest_framework.views import APIView


# Create your views here.
class RegisterUser(APIView):
    """
    Class for user registration.
    POST method only
    """

    def post(self, request):
        pass
