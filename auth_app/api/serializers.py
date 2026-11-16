"""Serializers for registration, login and user lookup."""

from django.contrib.auth import authenticate
from rest_framework import serializers

from auth_app.models import User


class UserSerializer(serializers.ModelSerializer):
    """Public user data used for members, assignees and reviewers."""

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']


class RegistrationSerializer(serializers.ModelSerializer):
    """Creates a new user account after validating the input."""

    password = serializers.CharField(write_only=True, min_length=8)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'repeated_password']

    def validate_fullname(self, value):
        """Require a first and last name, optionally with a middle name."""
        if len(value.split()) not in (2, 3):
            raise serializers.ValidationError(
                'Fullname must contain two or three words.'
            )
        return value

    def validate(self, attrs):
        """Ensure both password fields match."""
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError(
                {'repeated_password': 'Passwords do not match.'}
            )
        return attrs

    def create(self, validated_data):
        """Create the user with a hashed password."""
        validated_data.pop('repeated_password')
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Validates email and password and resolves the matching user."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate the credentials and attach the user."""
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid email or password.')

        if not user.check_password(password):
            raise serializers.ValidationError('Invalid email or password.')

        if not user.is_active:
            raise serializers.ValidationError('User account is disabled.')

        attrs['user'] = user
        return attrs

