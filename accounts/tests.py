from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class AccountTests(TestCase):
    def test_user_registration_can_create_user(self):
        user = User.objects.create_user(username='ada', email='ada@example.com', password='StrongPass123!')
        self.assertEqual(user.email, 'ada@example.com')

    def test_duplicate_email_is_not_allowed(self):
        User.objects.create_user(username='ada', email='ada@example.com', password='StrongPass123!')
        with self.assertRaises(Exception):
            User.objects.create_user(username='ada2', email='ada@example.com', password='StrongPass123!')
