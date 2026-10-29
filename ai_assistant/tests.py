from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from ai_assistant.models import ChatMessage

User = get_user_model()


@override_settings(AI_PROVIDER="none", AI_API_KEY="", GEMINI_API_KEY="")
class MoneyCoachFallbackTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="coach-user", email="coach@example.com", password="StrongPass123!")
        self.user.onboarding_completed = True
        self.user.save(update_fields=["onboarding_completed"])
        self.client.force_login(self.user)

    def test_chat_is_clear_when_live_ai_is_not_configured(self):
        response = self.client.get(reverse("ai_chat"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Preview mode")
        self.assertContains(response, "won't pretend a live AI response has been generated")

    def test_fallback_is_saved_to_the_member_chat_history(self):
        response = self.client.post(reverse("ai_chat"), {"prompt": "Help me plan food spending"})
        self.assertEqual(response.status_code, 302)
        saved = ChatMessage.objects.get(user=self.user)
        self.assertEqual(saved.prompt, "Help me plan food spending")
        self.assertIn("not connected to Gemini", saved.response)