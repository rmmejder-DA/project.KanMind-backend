"""Central URL configuration that routes each app under /api/."""

from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken import views as token_views

from core.views import api_index

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls, name='admin'),
    
    # Auth Token
    path('api/auth-token/', token_views.obtain_auth_token, name='api-token-auth'),
    
    # Authentication & User endpoints
    path('api/', include('auth_app.api.urls')),
    
    # Kanban Board, Task, Comment endpoints
    path('api/', include('kanban_app.api.urls')),
    
    # API Index
    path('', api_index, name='index'),
    
    # DRF auth UI
    path('api-auth/', include('rest_framework.urls')),
]

