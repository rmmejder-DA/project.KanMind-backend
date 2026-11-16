"""Index view listing the available API endpoints."""

from django.http import JsonResponse

ENDPOINTS = {
    'admin': '/admin/',
    'auth': {
        'registration': '/api/registration/',
        'login': '/api/login/',
        'guest-login': '/api/guest-login/',
        'token-auth': '/api/auth-token/',
        'email-check': '/api/email-check/',
    },
    'kanban': {
        'boards': '/api/boards/',
        'tasks': '/api/tasks/',
        'tasks-assigned-to-me': '/api/tasks/assigned-to-me/',
        'tasks-reviewing': '/api/tasks/reviewing/',
    },
}


def api_index(request):
    return JsonResponse({'endpoints': ENDPOINTS})


