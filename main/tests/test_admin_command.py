import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class EnsureAdminCommandTests(TestCase):
    def test_creates_superuser_from_environment(self):
        env = {
            "DJANGO_SUPERUSER_USERNAME": "bijiangcun",
            "DJANGO_SUPERUSER_EMAIL": "admin@example.com",
            "DJANGO_SUPERUSER_PASSWORD": "StrongPassword123!",
        }

        with patch.dict(os.environ, env, clear=False):
            call_command("ensure_admin", stdout=StringIO())

        user = get_user_model().objects.get(username="bijiangcun")
        self.assertEqual(user.email, "admin@example.com")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("StrongPassword123!"))

    def test_updates_existing_admin_without_creating_duplicate(self):
        User = get_user_model()
        User.objects.create_user(
            username="bijiangcun",
            email="old@example.com",
            password="old-password",
            is_staff=False,
            is_superuser=False,
        )
        env = {
            "DJANGO_SUPERUSER_USERNAME": "bijiangcun",
            "DJANGO_SUPERUSER_EMAIL": "new@example.com",
            "DJANGO_SUPERUSER_PASSWORD": "NewStrongPassword123!",
        }

        with patch.dict(os.environ, env, clear=False):
            call_command("ensure_admin", stdout=StringIO())

        self.assertEqual(User.objects.filter(username="bijiangcun").count(), 1)
        user = User.objects.get(username="bijiangcun")
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("NewStrongPassword123!"))

    def test_requires_password(self):
        env = {
            "DJANGO_SUPERUSER_USERNAME": "bijiangcun",
            "DJANGO_SUPERUSER_EMAIL": "admin@example.com",
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(CommandError):
                call_command("ensure_admin", stdout=StringIO())
