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
        """Return an example payload for the registration form."""
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
        """Create the user and return the token and user data."""
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
        """Return an example payload for the login form."""
        return Response(
            {
                "email": "max@example.com",
                "password": "Test123456",
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Authenticate the user and return the token and user data."""
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
        """Return the email of a non-staff user for the guest login."""
        guest_user = User.objects.filter(is_staff=False).first()

        if not guest_user:
            return Response(
                {"detail": "No guest user available."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"email": guest_user.email},
            status=status.HTTP_200_OK,
        )


class EmailCheckView(APIView):
    """Looks up a registered user by email address.

    GET takes the email as query parameter, POST takes it as JSON body
    ({"email": "..."}) so it can be sent without typing into a URL.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Check the email passed as query parameter."""
        return self.check_email(request.query_params.get("email"))

    def post(self, request):
        """Check the email passed in the JSON body."""
        data = request.data if isinstance(request.data, dict) else {}
        return self.check_email(data.get("email"))

    def check_email(self, email):
        """Validate the email and return the data of the matching user."""
        if not isinstance(email, str) or not email:
            return self.bad_request(
                "Email is required.",
                email="user@example.com",
            )

        if not self.is_valid_email(email):
            return self.bad_request("Invalid email address.")

        user = get_object_or_404(User, email=email)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    def is_valid_email(self, email):
        """Return True if the value is a syntactically valid email."""
        try:
            validate_email(email)
        except DjangoValidationError:
            return False
        return True

    def bad_request(self, detail, **extra):
        """Return a 400 response with a detail message and extra fields."""
        return Response(
            {"detail": detail, **extra},
            status=status.HTTP_400_BAD_REQUEST,
        )
