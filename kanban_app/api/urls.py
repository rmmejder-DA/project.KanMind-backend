"""URL routes for boards, tasks and task comments."""

from django.urls import path

from kanban_app.api.views import (
    AssignedTaskListView,
    BoardMembersListView,
    BoardViewSet,
    CommentViewSet,
    ReviewingTaskListView,
    TaskViewSet,
)

urlpatterns = [
    path(
        'boards/',
        BoardViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='board-list',
    ),
    path(
        'boards/<int:board_id>/members/',
        BoardMembersListView.as_view(),
        name='board-members',
    ),
    path(
        'boards/<int:pk>/',
        BoardViewSet.as_view({'get': 'retrieve', 'patch': 'update', 'delete': 'destroy'}),
        name='board-detail',
    ),
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
        'tasks/',
        TaskViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='task-list',
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
    path(
        'tasks/<int:pk>/',
        TaskViewSet.as_view({'get': 'retrieve', 'patch': 'update', 'delete': 'destroy'}),
        name='task-detail',
    ),
]
