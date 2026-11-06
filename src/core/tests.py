from django.test import TestCase
from django.urls import reverse


class WelcomePageTests(TestCase):
    def test_home_renders_the_tiana_welcome_screen(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/landing.html")
        self.assertContains(response, "TIANA — Your Money Friend Always")
        self.assertContains(response, "Take control")
        self.assertContains(response, "of your money")
        self.assertContains(response, "Track expenses, save for your goals")
        self.assertContains(response, reverse("onboarding"))
        self.assertContains(response, "assets/tiana-logo-transparent.png")
        self.assertContains(response, "assets/tiana-welcome-student-campus-4k.jpg")
        self.assertContains(
            response,
            'src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1554607983371431"',
        )
        self.assertNotContains(response, "assets/tiana-welcome-student-campus-4k.webp")
        self.assertNotContains(response, "welcome-status")
        self.assertNotContains(response, "welcome-time")

    def test_onboarding_is_a_three_slide_photo_flow_without_fake_status_bar(self):
        response = self.client.get(reverse("onboarding"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/onboarding.html")
        self.assertContains(response, "Take control of your money")
        self.assertContains(response, "Reach your goals faster")
        self.assertContains(response, "Make confident money decisions")
        self.assertContains(response, "assets/tiana-logo-transparent.png")
        self.assertContains(response, "assets/tiana-onboarding-money-clarity-4k.webp")
        self.assertContains(response, "assets/tiana-onboarding-savings-goals-4k.webp")
        self.assertContains(response, "assets/tiana-onboarding-ai-coach-4k.webp")
        self.assertContains(response, reverse("register"))
        self.assertNotContains(response, "onboarding-status")
        self.assertNotContains(response, "onboarding-status-icons")
        self.assertNotContains(response, "9:41")


class PWAOfflineAndPremiumTests(TestCase):
    def test_welcome_page_exposes_the_installable_pwa(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "manifest.webmanifest")
        self.assertContains(response, "tiana-install-button")
        self.assertContains(response, "nkem/pwa.js")

    def test_root_service_worker_is_served_with_root_scope_permission(self):
        response = self.client.get(reverse("service_worker"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("javascript", response["Content-Type"])
        self.assertEqual(response["Service-Worker-Allowed"], "/")
        self.assertContains(response, "tiana-pwa-shell-v1")
        self.assertNotContains(response, "caches.put(event.request")

    def test_offline_bootstrap_requires_a_signed_in_member(self):
        response = self.client.get(reverse("offline_bootstrap"))
        self.assertEqual(response.status_code, 302)

    def test_offline_bootstrap_contains_only_the_signed_in_members_snapshot(self):
        from django.contrib.auth import get_user_model
        from finance.models import Account

        user = get_user_model().objects.create_user(
            username="offline-member",
            email="offline-member@example.com",
            password="StrongPass123!",
        )
        Account.objects.create(owner=user, name="Daily cash", opening_balance="2500", balance="2500")
        self.client.force_login(user)
        response = self.client.get(reverse("offline_bootstrap"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store, max-age=0")
        self.assertEqual(response.json()["accounts"][0]["name"], "Daily cash")

    def test_premium_page_explains_the_current_checkout_status(self):
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user(
            username="premium-member",
            email="premium-member@example.com",
            password="StrongPass123!",
        )
        self.client.force_login(user)
        response = self.client.get(reverse("premium"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "3 AI coach requests per day")
        self.assertContains(response, "20 AI coach requests per day")
        self.assertContains(response, "Premium checkout is not connected yet")


    def test_money_school_exposes_the_adsense_verification_code_but_no_ad_units(self):
        response = self.client.get(reverse("money_school"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student Money School")
        self.assertContains(response, "budget")
        self.assertContains(
            response,
            'src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1554607983371431"',
        )
        self.assertNotContains(response, '<ins class="adsbygoogle"')

    def test_authenticated_financial_pages_do_not_load_the_adsense_script(self):
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user(
            username="ads-private-member",
            email="ads-private-member@example.com",
            password="StrongPass123!",
            onboarding_completed=True,
        )
        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "pagead2.googlesyndication.com")


class MoneyIntelligenceTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from django.utils import timezone

        self.today = timezone.localdate()
        self.user = get_user_model().objects.create_user(
            username="money-intelligence-member",
            email="money-intelligence@example.com",
            password="StrongPass123!",
            currency="XAF",
            onboarding_completed=True,
        )

    def create_account(self, name, amount, currency="XAF", account_type="cash"):
        from finance.models import Account

        return Account.objects.create(
            owner=self.user,
            name=name,
            account_type=account_type,
            currency=currency,
            opening_balance=amount,
            balance=amount,
        )

    def create_transaction(self, account, amount, kind, category, description=""):
        from finance.models import Transaction

        return Transaction.objects.create(
            owner=self.user,
            account=account,
            amount=amount,
            currency=account.currency,
            kind=kind,
            category=category,
            description=description,
            transaction_date=self.today,
        )

    def test_safe_to_spend_protects_only_the_unfunded_weekly_savings_target(self):
        from decimal import Decimal
        from core.money_intelligence import build_money_snapshot

        self.user.weekly_savings_target = Decimal("2000.00")
        self.user.save(update_fields=["weekly_savings_target"])
        cash = self.create_account("Daily cash", "10000.00")
        self.create_account("Long-term savings", "25000.00", account_type="savings")
        self.create_account("Dollar wallet", "50.00", currency="USD")
        self.create_transaction(cash, "500.00", "transfer_out", "Savings", "Goal top-up")

        snapshot = build_money_snapshot(self.user, today=self.today)

        self.assertEqual(snapshot["currency"], "XAF")
        self.assertEqual(snapshot["spendable_balance"], Decimal("9500.00"))
        self.assertEqual(snapshot["total_balance"], Decimal("34500.00"))
        self.assertEqual(snapshot["weekly_savings_funded"], Decimal("500.00"))
        self.assertEqual(snapshot["weekly_savings_remaining"], Decimal("1500.00"))
        self.assertEqual(snapshot["safe_to_spend"], Decimal("8000.00"))
        self.assertEqual(snapshot["other_currency_account_count"], 1)

    def test_monthly_cash_flow_does_not_count_transfers_as_income_or_expenses(self):
        from decimal import Decimal
        from core.money_intelligence import build_money_snapshot

        cash = self.create_account("Daily cash", "10000.00")
        self.create_transaction(cash, "5000.00", "income", "Allowance")
        self.create_transaction(cash, "1200.00", "expense", "Food")
        self.create_transaction(cash, "400.00", "transfer_out", "Transfer")

        snapshot = build_money_snapshot(self.user, today=self.today)

        self.assertEqual(snapshot["income_total"], Decimal("5000.00"))
        self.assertEqual(snapshot["money_in_total"], Decimal("5000.00"))
        self.assertEqual(snapshot["expense_total"], Decimal("1200.00"))
        self.assertEqual(snapshot["net_cash_flow"], Decimal("3800.00"))

    def test_weekly_budget_progress_uses_recorded_expenses_in_the_same_currency(self):
        from decimal import Decimal
        from budgets.models import Budget
        from core.money_intelligence import build_money_snapshot

        cash = self.create_account("Daily cash", "10000.00")
        budget = Budget.objects.create(
            owner=self.user,
            name="Food",
            category="Food",
            amount="3000.00",
            currency="XAF",
            period="weekly",
            start_date=self.today,
        )
        self.create_transaction(cash, "1200.00", "expense", "Food")

        snapshot = build_money_snapshot(self.user, today=self.today)

        self.assertEqual(len(snapshot["weekly_budgets"]), 1)
        self.assertEqual(snapshot["weekly_budgets"][0].pk, budget.pk)
        self.assertEqual(snapshot["weekly_budget_spent"], Decimal("1200.00"))
        self.assertEqual(snapshot["weekly_budget_remaining"], Decimal("1800.00"))
        self.assertEqual(snapshot["budget_usage_percent"], 40)

    def test_dashboard_uses_the_live_money_intelligence_snapshot(self):
        from finance.models import Account

        Account.objects.create(
            owner=self.user,
            name="Daily cash",
            account_type="cash",
            currency="XAF",
            opening_balance="10000.00",
            balance="10000.00",
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SAFE TO SPEND THIS WEEK")
        self.assertContains(response, "A gentle daily guide")
        self.assertContains(response, "YOUR WEEKLY PLAN")
        self.assertContains(response, "Your money flow")
        self.assertContains(response, "Transfers between your own accounts")


class AccountsCentreTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        self.user = get_user_model().objects.create_user(
            username="account-centre-member",
            email="account-centre@example.com",
            password="StrongPass123!",
            currency="XAF",
        )

    def test_accounts_are_grouped_by_currency_and_private_to_the_member(self):
        from finance.models import Account
        from django.contrib.auth import get_user_model

        Account.objects.create(
            owner=self.user, name="Pocket cash", account_type="cash",
            currency="XAF", opening_balance="2500.00", balance="2500.00",
        )
        Account.objects.create(
            owner=self.user, name="Savings reserve", account_type="savings",
            currency="XAF", opening_balance="10000.00", balance="10000.00",
        )
        Account.objects.create(
            owner=self.user, name="Dollar wallet", account_type="bank",
            currency="USD", opening_balance="50.00", balance="50.00",
        )
        other = get_user_model().objects.create_user(
            username="another-member", email="another-member@example.com",
            password="StrongPass123!",
        )
        Account.objects.create(
            owner=other, name="Private account", account_type="cash",
            currency="XAF", opening_balance="900000.00", balance="900000.00",
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pocket cash")
        self.assertContains(response, "Savings reserve")
        self.assertContains(response, "Dollar wallet")
        self.assertContains(response, "XAF")
        self.assertContains(response, "USD")
        self.assertNotContains(response, "Private account")
        self.assertEqual(len(response.context["account_groups"]), 2)
        self.assertEqual(response.context["primary_total_balance"], 12500)

    def test_accounts_centre_requires_authentication(self):
        response = self.client.get(reverse("accounts"))
        self.assertEqual(response.status_code, 302)


class BudgetIntelligencePageTests(TestCase):
    def test_budget_page_shows_live_weekly_pulse_from_real_transactions(self):
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        from budgets.models import Budget
        from finance.models import Account, Transaction

        user = get_user_model().objects.create_user(
            username="budget-pulse-member",
            email="budget-pulse@example.com",
            password="StrongPass123!",
            currency="XAF",
        )
        account = Account.objects.create(
            owner=user, name="Daily cash", account_type="cash", currency="XAF",
            opening_balance="10000.00", balance="10000.00",
        )
        Budget.objects.create(
            owner=user, name="Food", category="Food", amount="3000.00",
            currency="XAF", period="weekly", start_date=timezone.localdate(),
        )
        Transaction.objects.create(
            owner=user, account=account, amount="1200.00", currency="XAF",
            kind="expense", category="Food", transaction_date=timezone.localdate(),
        )
        self.client.force_login(user)

        response = self.client.get(reverse("budgets"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LIVE WEEKLY PULSE")
        from decimal import Decimal
        self.assertEqual(response.context["weekly_spent"], Decimal("1200.00"))
        self.assertEqual(response.context["weekly_planned"], Decimal("3000.00"))
        self.assertContains(response, "40% of weekly limits used")

class MoneySchoolGuideTests(TestCase):
    def test_public_money_school_guides_are_complete_and_cross_linked(self):
        expected = {
            "weekly-budget": "Build a weekly student budget that works in real life",
            "savings-goals": "Turn a savings goal into a plan you can follow",
            "mobile-money-safety": "Protect your Mobile Money and digital accounts",
            "variable-income": "Plan when your student income changes from week to week",
        }
        for slug, title in expected.items():
            with self.subTest(slug=slug):
                response = self.client.get(reverse("money_school_guide", kwargs={"slug": slug}))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "core/money_school_guide.html")
                self.assertContains(response, title)
                self.assertContains(response, "THE TAKEAWAY")
                self.assertContains(response, "Back to Money School")
                self.assertContains(response, 'rel="canonical"')

        index = self.client.get(reverse("money_school"))
        self.assertEqual(index.status_code, 200)
        for slug in expected:
            self.assertContains(index, reverse("money_school_guide", kwargs={"slug": slug}))

    def test_money_school_guides_are_in_the_public_sitemap(self):
        response = self.client.get(reverse("sitemap_xml"))
        self.assertEqual(response.status_code, 200)
        sitemap = response.content.decode()
        for slug in ("weekly-budget", "savings-goals", "mobile-money-safety", "variable-income"):
            self.assertIn(
                "https://tiana.lol" + reverse("money_school_guide", kwargs={"slug": slug}),
                sitemap,
            )

    def test_unknown_money_school_guide_returns_a_real_404(self):
        response = self.client.get(reverse("money_school_guide", kwargs={"slug": "not-a-guide"}))
        self.assertEqual(response.status_code, 404)

