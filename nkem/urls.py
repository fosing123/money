from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from accounts.views import login_view, logout_view, onboarding_view, profile_view, register_view
from ai_assistant.views import ai_chat_view
from budgets.views import budget_create_view, budget_list_view
from core.views import dashboard_view, health_check_view, home_view
from finance.views import transaction_create_view, transaction_delete_view, transaction_list_view, transaction_update_view
from goals.views import goal_create_view, goal_list_view

urlpatterns = [
    path('', home_view, name='home'),
    path('onboarding/', onboarding_view, name='onboarding'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('transactions/', transaction_list_view, name='transactions'),
    path('transactions/new/', transaction_create_view, name='transaction_create'),
    path('transactions/<int:pk>/edit/', transaction_update_view, name='transaction_update'),
    path('transactions/<int:pk>/delete/', transaction_delete_view, name='transaction_delete'),
    path('budgets/', budget_list_view, name='budgets'),
    path('budgets/new/', budget_create_view, name='budget_create'),
    path('goals/', goal_list_view, name='goals'),
    path('goals/new/', goal_create_view, name='goal_create'),
    path('ai/', ai_chat_view, name='ai_chat'),
    path('health/', health_check_view, name='health_check'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
