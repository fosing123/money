from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list_view(request):
    items = Notification.objects.filter(user=request.user)
    return render(request, "notifications/list.html", {"notifications": items})


@login_required
@require_POST
def mark_notification_read_view(request, pk):
    Notification.objects.filter(pk=pk, user=request.user).update(is_read=True)
    return redirect("notifications")


@login_required
@require_POST
def mark_all_notifications_read_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect("notifications")