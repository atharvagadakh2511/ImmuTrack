from django.test import TestCase
from django.contrib.auth.models import User
from .models import Role, Clinic

class AccountsTestCase(TestCase):
    def setUp(self):
        self.clinic = Clinic.objects.create(
            name="Test PHC",
            registration_code="TEST-01",
            address="123 Hospital Road",
            contact_phone="1234567890",
            contact_email="test@clinic.org"
        )
        self.user = User.objects.create_user(username="parent_test", password="Password@123")

    def test_user_profile_creation(self):
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertEqual(self.user.profile.role, Role.PARENT)

    def test_role_properties(self):
        profile = self.user.profile
        self.assertTrue(profile.is_parent)
        self.assertFalse(profile.is_health_worker)
        self.assertFalse(profile.is_admin)
