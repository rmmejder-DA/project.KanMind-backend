"""Serializers for registration, login and user lookup."""

from django.contrib.auth import authenticate
from rest_framework import serializers

from auth_app.models import User


class UserSerializer(serializers.ModelSerializer):
    """Public user data used for members, assignees and reviewers."""

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]


class RegistrationSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(initial="Max Mustermann")
    email = serializers.EmailField(initial="max@example.com")
    password = serializers.CharField(
        write_only=True,
        initial="Test123456"
    )
    repeated_password = serializers.CharField(
        write_only=True,
        initial="Test123456"
    )

    class Meta:
        model = User
        fields = [
            "fullname",
            "email",
            "password",
            "repeated_password",
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("repeated_password")

        user = User(
            email=validated_data["email"],
            fullname=validated_data["fullname"],
        )

        user.set_password(validated_data["password"])
        user.save()

        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            email=attrs["email"],
            password=attrs["password"]
        )

        if user is None:
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "User account is disabled."
            )

        attrs["user"] = user
        return attrs