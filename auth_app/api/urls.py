"""URL routes for the authentication endpoints."""

from django.urls import path

from auth_app.api.views import (
    EmailCheckView,
    GuestLoginView,
    LoginView,
    RegistrationView,
)

urlpatterns = [
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('login/', LoginView.as_view(), name='login'),
    path('guest-login/', GuestLoginView.as_view(), name='guest-login'),
    path('email-check/', EmailCheckView.as_view(), name='email-check'),
]
