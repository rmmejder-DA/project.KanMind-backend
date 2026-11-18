"""Views for registration, login and email lookup."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.api.serializers import (
    LoginSerializer,
    RegistrationSerializer,
    UserSerializer,
)
from auth_app.models import User


def build_auth_payload(user, token):
    """Return the data the frontend stores after login or registration."""
    return {
        "token": token.key,
        "user_id": user.id,
        "email": user.email,
        "fullname": user.fullname,
    }


class RegistrationView(APIView):
    """Creates a user account and returns an API token."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "fullname": "Max Mustermann",
                "email": "max@example.com",
                "password": "Test123456",
                "repeated_password": "Test123456",
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            build_auth_payload(user, token),
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticates a user by email and password."""

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def get(self, request):
        return Response(
            {
                "email": "max@example.com",
                "password": "Test123456",
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            build_auth_payload(user, token),
            status=status.HTTP_200_OK,
        )


class GuestLoginView(APIView):
    """Guest login without authentication."""

    permission_classes = [AllowAny]

    def get(self, request):
        guest_user = User.objects.filter(is_staff=False).first()

        if not guest_user:
            return Response(
                {"detail": "No guest user available."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "email": guest_user.email,
                "password": "asdasdasd"
            },
            status=status.HTTP_200_OK,
        )


class EmailCheckView(APIView):
    """Looks up a registered user by email address."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        email = request.query_params.get("email")

        if not email:
            return Response(
                {"detail": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_email(email)
        except DjangoValidationError:
            return Response(
                {"detail": "Invalid email address."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = get_object_or_404(
            User,
            email=email,
        )

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_200_OK,
        )