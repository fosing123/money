from django.urls import path

from .views import analyzer_view


urlpatterns = [
    path("", analyzer_view, name="analyzer"),
]
