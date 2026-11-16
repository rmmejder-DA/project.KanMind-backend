"""User model that authenticates with an email address."""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """Manager for users identified by their email address."""

    def create_user(self, email, fullname, password=None):
        """Create and save a regular user."""
        if not email:
            raise ValueError('An email address is required.')
        user = self.model(email=self.normalize_email(email), fullname=fullname)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, fullname, password=None):
        """Create and save a superuser."""
        user = self.create_user(email, fullname, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Account used to log in and to collaborate on boards."""

    email = models.EmailField(unique=True)
    fullname = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['fullname']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['fullname']

    def __str__(self):
        return self.email
