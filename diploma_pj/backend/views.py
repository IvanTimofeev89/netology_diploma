from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .permissions import EmailPasswordPermission
from .serializers import ContactSerializer, UserSerializer


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


class CreateContact(APIView):
    """
    Class for contact creation.
    """

    permission_classes = [EmailPasswordPermission]

    def post(self, request):
        serializer = ContactSerializer(data=request.data, context={"user": request.user})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse({"message": "Contact created successfully"})
