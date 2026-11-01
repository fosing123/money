from django.test import TestCase
from django.urls import reverse

from .models import Opportunity


class OpportunityListingTests(TestCase):
    def test_active_opportunities_are_visible_and_inactive_are_hidden(self):
        active = Opportunity.objects.create(name="Laptop repair", category="Tech", description="Student-friendly repair service", is_active=True)
        Opportunity.objects.create(name="Hidden offer", category="Tech", description="Not published", is_active=False)
        response = self.client.get(reverse("opportunities"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, active.name)
        self.assertNotContains(response, "Hidden offer")

    def test_search_filters_opportunities(self):
        Opportunity.objects.create(name="Laptop repair", category="Tech", description="Repair service")
        Opportunity.objects.create(name="Math tutoring", category="Education", description="Help with homework")
        response = self.client.get(reverse("opportunities"), {"q": "tutoring"})
        self.assertContains(response, "Math tutoring")
        self.assertNotContains(response, "Laptop repair")