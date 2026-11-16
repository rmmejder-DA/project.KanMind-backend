"""Central URL configuration that routes each app under /api/."""

from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken import views as token_views

from core.views import api_index

urlpatterns = [
    path('', api_index, name='index'),
    path('admin/', admin.site.urls),
    path('api/', api_index, name='api-index'),
    path('api/auth-token/', token_views.obtain_auth_token, name='api-token-auth'),
    path('api-auth/', include('rest_framework.urls')),
    path('api/', include('auth_app.api.urls')),
    path('api/', include('kanban_app.api.urls')),
]
