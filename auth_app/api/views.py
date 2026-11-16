"""Views for registration, login and email lookup."""

from django.shortcuts import get_object_or_404
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
        'token': token.key,
        'user_id': user.id,
        'email': user.email,
        'fullname': user.fullname,
    }


class RegistrationView(APIView):
    """Creates a user account and returns an API token."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Validate the input, create the user and return the token."""
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = Token.objects.create(user=user)
        return Response(build_auth_payload(user, token), status=201)


class LoginView(APIView):
    """Authenticates a user by email and password."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Return the API token for valid credentials."""
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response(build_auth_payload(user, token))


class EmailCheckView(APIView):
    """Looks up a registered user by email address."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return the user for the email query parameter or 404."""
        user = get_object_or_404(
            User,
            email=request.query_params.get('email', ''),
        )
        return Response(UserSerializer(user).data)
