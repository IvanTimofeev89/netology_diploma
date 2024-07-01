from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import Contact, User


class RegisterUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "middle_name", "company", "position")

    def validate(self, data):
        password = self.initial_data.get("password")
        email = self.initial_data.get("email")

        if not password:
            raise serializers.ValidationError("Password is required")
        if not email:
            raise serializers.ValidationError("Email is required")
        try:
            validated_password = validate_password(password)
        except ValidationError as error:
            raise serializers.ValidationError({"password": error})
        data["password"] = validated_password
        return data

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ContactCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ("id", "city", "street", "house", "structure", "building", "apartment", "phone")
        read_only_fields = ("id",)

    def create(self, validated_data):
        validated_data["user"] = self.context["user"]
        return Contact.objects.create(**validated_data)


class ContactUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ("city", "street", "house", "structure", "building", "apartment", "phone")

    def create(self, validated_data):
        validated_data["user"] = self.context["user"]
        return Contact.objects.filter(user=self.context["user"]).update(**validated_data)


class ContactRetrieveSerializer(serializers.ModelSerializer):
    user = RegisterUserSerializer()

    class Meta:
        model = Contact
        fields = ("user", "city", "street", "house", "structure", "building", "apartment", "phone")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "company", "position")


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "middle_name", "company", "position")

    def create(self, validated_data):
        email = self.context["email"]
        return User.objects.filter(email=email).update(**validated_data)
