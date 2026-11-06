from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, reverse_lazy
from django.contrib.auth.views import PasswordChangeDoneView, PasswordChangeView

from accounts.views import application_security_view, login_view, logout_view, manage_devices_view, onboarding_setup_view, onboarding_view, profile_view, register_view, registration_welcome_view
from expense_analyzer.views import analyzer_insight_view, analyzer_personalization_view, analyzer_transaction_preview_view, analyzer_view
from budgets.views import budget_allocations_view, budget_delete_view, budget_list_view
from core.views import dashboard_view, health_check_view, home_view, investments_coming_soon_view, money_school_view, offline_bootstrap_view, offline_sync_view, premium_view, service_worker_view
from finance.views import account_list_view, account_create_view, transaction_create_view, transaction_delete_view, transaction_export_view, transaction_list_view, transaction_update_view
from goals.views import goal_contribute_view, goal_create_view, goal_delete_view, goal_list_view
from insights.views import insights_view
from marketplace.views import opportunity_detail_view, opportunity_list_view
from notifications.views import mark_all_notifications_read_view, mark_notification_read_view, notification_list_view
from notifications.api import backup_export_view, backup_restore_view, register_push_device_view, unregister_push_device_view
from notifications.config import firebase_web_config_view

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
    path("profile/security/", application_security_view, name="application_security"),
    path("profile/devices/", manage_devices_view, name="manage_devices"),
    path("profile/password/", PasswordChangeView.as_view(template_name="accounts/password_change_form.html", success_url=reverse_lazy("password_change_done")), name="password_change"),
    path("profile/password/done/", PasswordChangeDoneView.as_view(template_name="accounts/password_change_done.html"), name="password_change_done"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("accounts/", account_list_view, name="accounts"),
    path("accounts/new/", account_create_view, name="account_create"),
    path("transactions/", transaction_list_view, name="transactions"),
    path("transactions/export.csv", transaction_export_view, name="transaction_export"),
    path("transactions/new/", transaction_create_view, name="transaction_create"),
    path("transactions/<int:pk>/edit/", transaction_update_view, name="transaction_update"),
    path("transactions/<int:pk>/delete/", transaction_delete_view, name="transaction_delete"),
    path("budgets/", budget_list_view, name="budgets"),
    path("budgets/allocations/", budget_allocations_view, name="budget_allocations"),
    path("budgets/<int:pk>/delete/", budget_delete_view, name="budget_delete"),
    path("goals/", goal_list_view, name="goals"),
    path("goals/new/", goal_create_view, name="goal_create"),
    path("goals/<int:pk>/add/", goal_contribute_view, name="goal_contribute"),
    path("goals/<int:pk>/delete/", goal_delete_view, name="goal_delete"),
    path("insights/", insights_view, name="insights"),
    path("notifications/", notification_list_view, name="notifications"),
    path("firebase-config.js", firebase_web_config_view, name="firebase_web_config"),
    path("api/push/register/", register_push_device_view, name="push_register"),
    path("api/push/unregister/", unregister_push_device_view, name="push_unregister"),
    path("api/backup/export/", backup_export_view, name="backup_export"),
    path("api/backup/restore/", backup_restore_view, name="backup_restore"),
    path("notifications/<int:pk>/read/", mark_notification_read_view, name="notification_mark_read"),
    path("notifications/read-all/", mark_all_notifications_read_view, name="notifications_mark_all_read"),
    path("opportunities/", opportunity_list_view, name="opportunities"),
    path("invest/", investments_coming_soon_view, name="investments"),
    path("premium/", premium_view, name="premium"),
    path("money-school/", money_school_view, name="money_school"),
    path("opportunities/<int:pk>/", opportunity_detail_view, name="opportunity_detail"),
    path("analyzer/transaction-preview/", analyzer_transaction_preview_view, name="analyzer_transaction_preview"),
    path("analyzer/insight/", analyzer_insight_view, name="analyzer_insight"),
    path("analyzer/personalization/", analyzer_personalization_view, name="analyzer_personalization"),
    path("analyzer/", analyzer_view, name="analyzer"),
    path("ai/", analyzer_view, name="ai_chat"),  # Legacy URL now opens the Expense Analyzer.
    path("health/", health_check_view, name="health_check"),
    path("service-worker.js", service_worker_view, name="service_worker"),
    path("api/offline/bootstrap/", offline_bootstrap_view, name="offline_bootstrap"),
    path("api/offline/sync/", offline_sync_view, name="offline_sync"),
    path("admin/", admin.site.urls),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)