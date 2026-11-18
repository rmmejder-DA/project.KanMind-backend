"""Tests for the authentication endpoints."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

User = get_user_model()

REGISTRATION_URL = '/api/registration/'
LOGIN_URL = '/api/login/'
EMAIL_CHECK_URL = '/api/email-check/'


class AuthApiTests(TestCase):
    """Covers registration, login and email check."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='anna@example.com',
            password='secret123',
            fullname='Anna Meier',
        )

    def test_registration_creates_user_and_returns_token(self):
        response = self.client.post(REGISTRATION_URL, {
            'fullname': 'Max Mustermann',
            'email': 'max@example.com',
            'password': 'strongpass',
            'repeated_password': 'strongpass',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['email'], 'max@example.com')
        self.assertTrue(User.objects.filter(email='max@example.com').exists())

    def test_registration_rejects_mismatched_passwords(self):
        response = self.client.post(REGISTRATION_URL, {
            'fullname': 'Max Mustermann',
            'email': 'max@example.com',
            'password': 'strongpass',
            'repeated_password': 'otherpass',
        }, format='json')

        self.assertEqual(response.status_code, 400)

    def test_registration_rejects_single_word_fullname(self):
        response = self.client.post(REGISTRATION_URL, {
            'fullname': 'Max',
            'email': 'max@example.com',
            'password': 'strongpass',
            'repeated_password': 'strongpass',
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('fullname', response.data)

    def test_login_returns_token_and_user_data(self):
        response = self.client.post(LOGIN_URL, {
            'email': 'anna@example.com',
            'password': 'secret123',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user_id'], self.user.id)
        self.assertEqual(response.data['fullname'], 'Anna Meier')
        self.assertTrue(
            Token.objects.filter(user=self.user, key=response.data['token'])
            .exists()
        )

    def test_login_rejects_wrong_password(self):
        response = self.client.post(LOGIN_URL, {
            'email': 'anna@example.com',
            'password': 'wrong',
        }, format='json')

        self.assertEqual(response.status_code, 400)

    def test_email_check_returns_user_for_known_email(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(EMAIL_CHECK_URL, {'email': self.user.email})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.user.id)

    def test_email_check_returns_404_for_unknown_email(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(EMAIL_CHECK_URL, {'email': 'nobody@x.de'})

        self.assertEqual(response.status_code, 404)

    def test_email_check_rejects_missing_or_malformed_email(self):
        self.client.force_authenticate(user=self.user)

        missing = self.client.get(EMAIL_CHECK_URL)
        malformed = self.client.get(EMAIL_CHECK_URL, {'email': 'not-an-email'})

        self.assertEqual(missing.status_code, 400)
        self.assertEqual(malformed.status_code, 400)
