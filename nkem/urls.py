from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from accounts.views import login_view, logout_view, onboarding_setup_view, onboarding_view, profile_view, register_view, registration_welcome_view
from ai_assistant.views import ai_chat_view
from budgets.views import budget_create_view, budget_list_view
from core.views import dashboard_view, health_check_view, home_view
from finance.views import account_create_view, transaction_create_view, transaction_delete_view, transaction_list_view, transaction_update_view
from goals.views import goal_create_view, goal_list_view
from insights.views import insights_view
from marketplace.views import opportunity_detail_view, opportunity_list_view
from notifications.views import mark_all_notifications_read_view, mark_notification_read_view, notification_list_view

admin.site.site_header = "TIANA Control Center"
admin.site.site_title = "TIANA Admin"
admin.site.index_title = "Manage the TIANA experience"

urlpatterns = [
    path("", home_view, name="home"),
    path("onboarding/", onboarding_view, name="onboarding"),
    path("setup/", onboarding_setup_view, name="onboarding_setup"),
    path("register/", register_view, name="register"),
    path("welcome/", registration_welcome_view, name="registration_welcome"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("accounts/new/", account_create_view, name="account_create"),
    path("transactions/", transaction_list_view, name="transactions"),
    path("transactions/new/", transaction_create_view, name="transaction_create"),
    path("transactions/<int:pk>/edit/", transaction_update_view, name="transaction_update"),
    path("transactions/<int:pk>/delete/", transaction_delete_view, name="transaction_delete"),
    path("budgets/", budget_list_view, name="budgets"),
    path("budgets/new/", budget_create_view, name="budget_create"),
    path("goals/", goal_list_view, name="goals"),
    path("goals/new/", goal_create_view, name="goal_create"),
    path("insights/", insights_view, name="insights"),
    path("notifications/", notification_list_view, name="notifications"),
    path("notifications/<int:pk>/read/", mark_notification_read_view, name="notification_mark_read"),
    path("notifications/read-all/", mark_all_notifications_read_view, name="notifications_mark_all_read"),
    path("opportunities/", opportunity_list_view, name="opportunities"),
    path("opportunities/<int:pk>/", opportunity_detail_view, name="opportunity_detail"),
    path("ai/", ai_chat_view, name="ai_chat"),
    path("health/", health_check_view, name="health_check"),
    path("admin/", admin.site.urls),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)