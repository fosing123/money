from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ChatMessage

User = get_user_model()


class AIChatSafetyTests(TestCase):
    @override_settings(GEMINI_API_KEY="", AI_API_KEY="", AI_PROVIDER="gemini")
    def test_unconfigured_coach_discloses_preview_mode_instead_of_claiming_live_ai(self):
        user = User.objects.create_user(username="ai-user", email="ai@example.test", password="Saffron-Planet-2026!")
        self.client.force_login(user)
        response = self.client.post(reverse("ai_chat"), {"prompt": "Help me make a budget"})
        self.assertRedirects(response, reverse("ai_chat"))
        entry = ChatMessage.objects.get(user=user)
        self.assertIn("not connected to Gemini", entry.response)
        self.assertNotIn("I generated this with Gemini", entry.response)