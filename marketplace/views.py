from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Opportunity


def opportunity_list_view(request):
    opportunities = Opportunity.objects.filter(is_active=True)
    search = request.GET.get("q", "").strip()[:100]
    kind = request.GET.get("kind", "").strip()
    if search:
        opportunities = opportunities.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(category__icontains=search) |
            Q(location__icontains=search)
        )
    if kind in dict(Opportunity.KIND_CHOICES):
        opportunities = opportunities.filter(kind=kind)
    categories = Opportunity.objects.filter(is_active=True).values_list("category", flat=True).distinct().order_by("category")
    return render(request, "marketplace/opportunities.html", {
        "opportunities": opportunities,
        "search": search,
        "selected_kind": kind,
        "kind_choices": Opportunity.KIND_CHOICES,
        "categories": categories,
    })


def opportunity_detail_view(request, pk):
    opportunity = get_object_or_404(Opportunity, pk=pk, is_active=True)
    return render(request, "marketplace/opportunity_detail.html", {"opportunity": opportunity})