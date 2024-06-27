from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import Contact, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name")
        read_only_fields = ("id",)

    def validate(self, data):
        password = self.initial_data.get("password")
        if not password:
            raise serializers.ValidationError("Password is required")
        try:
            validate_password(password)
        except ValidationError as error:
            raise serializers.ValidationError({"password": error})
        return data

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "phone"
        read_only_fields = ("id",)
