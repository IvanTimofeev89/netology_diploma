from django.http import JsonResponse
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .models import Contact
from .permissions import EmailOrTokenPermission, EmailPasswordPermission
from .serializers import (
    ContactCreateSerializer,
    ContactRetrieveSerializer,
    UserSerializer,
)


class LoginView(APIView):
    """
    Class to achieve Token by provided user's email and password.
    """

    permission_classes = [EmailPasswordPermission]

    def post(self, request):
        user = request.user
        token, created = Token.objects.get_or_create(user=user)
        return JsonResponse({"token": token.key})


class RegisterUser(APIView):
    """
    Class for user registration.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            user.set_password(request.data["password"])
            user.save()
            return JsonResponse({"message": "User created successfully"})


class ManageContact(APIView):
    """
    Class for contact creation.
    """

    permission_classes = [EmailOrTokenPermission]

    def post(self, request):
        serializer = ContactCreateSerializer(data=request.data, context={"user": request.user})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse({"message": "Contact created successfully"})
        else:
            return JsonResponse({"message": serializer.errors})

    def get(self, request):
        user_contacts = Contact.objects.all()
        serializer = ContactRetrieveSerializer(user_contacts, many=True)
        return JsonResponse(serializer.data, safe=False)

    # def get_permissions(self):
    #     if self.request.method == 'POST':
    #         return [EmailPasswordPermission()]
    #     if self.request.method == 'GET':
    #         return [IsOwnerOrAdminPermission()]
    #     return super().get_permissions()
