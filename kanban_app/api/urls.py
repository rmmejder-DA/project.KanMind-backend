"""URL routes for boards, tasks and task comments."""

from django.urls import path
from rest_framework.routers import SimpleRouter

from kanban_app.api.views import (
    AssignedTaskListView,
    BoardViewSet,
    CommentViewSet,
    ReviewingTaskListView,
    TaskViewSet,
)

router = SimpleRouter()
router.register('boards', BoardViewSet, basename='board')
router.register('tasks', TaskViewSet, basename='task')

urlpatterns = [
    path(
        'tasks/assigned-to-me/',
        AssignedTaskListView.as_view(),
        name='tasks-assigned',
    ),
    path(
        'tasks/reviewing/',
        ReviewingTaskListView.as_view(),
        name='tasks-reviewing',
    ),
    path(
        'tasks/<int:task_id>/comments/',
        CommentViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='task-comments',
    ),
    path(
        'tasks/<int:task_id>/comments/<int:pk>/',
        CommentViewSet.as_view({'delete': 'destroy'}),
        name='task-comment-detail',
    ),
] + router.urls
