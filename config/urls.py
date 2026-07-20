"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from main.admin import data_overview
from main.admin_ai_views import (
    ai_analytics_page,
    ask_conversation,
    conversation_detail,
    create_conversation,
    delete_conversation,
    retry_turn,
)

urlpatterns = [
    path(
        "admin/ai-analytics/",
        admin.site.admin_view(ai_analytics_page),
        name="admin_ai_analytics",
    ),
    path(
        "admin/ai-analytics/conversations/",
        admin.site.admin_view(create_conversation),
        name="admin_ai_conversation_create",
    ),
    path(
        "admin/ai-analytics/conversations/<int:conversation_id>/",
        admin.site.admin_view(conversation_detail),
        name="admin_ai_conversation_detail",
    ),
    path(
        "admin/ai-analytics/conversations/<int:conversation_id>/delete/",
        admin.site.admin_view(delete_conversation),
        name="admin_ai_conversation_delete",
    ),
    path(
        "admin/ai-analytics/conversations/<int:conversation_id>/ask/",
        admin.site.admin_view(ask_conversation),
        name="admin_ai_conversation_ask",
    ),
    path(
        "admin/ai-analytics/turns/<int:turn_id>/retry/",
        admin.site.admin_view(retry_turn),
        name="admin_ai_turn_retry",
    ),
    path(
        "admin/data-overview/",
        admin.site.admin_view(data_overview),
        name="admin_data_overview",
    ),
    path("admin/", admin.site.urls),
    path("api/v1/", include("main.api_urls")),
    path("", TemplateView.as_view(template_name="index.html"), name="frontend"),
]
