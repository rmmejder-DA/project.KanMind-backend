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
    # Boards
    path(
        'boards/',
        BoardViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='board-list',
    ),
    path(
        'boards/<int:pk>/',
        BoardViewSet.as_view({'get': 'retrieve', 'patch': 'update', 'delete': 'destroy'}),
        name='board-detail',
    ),
    path(
        'boards/<int:board_id>/members/',
        BoardMembersListView.as_view(),
        name='board-members',
    ),
    
    # Tasks
    path(
        'tasks/',
        TaskViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='task-list',
    ),
    path(
        'tasks/<int:pk>/',
        TaskViewSet.as_view({'get': 'retrieve', 'patch': 'update', 'delete': 'destroy'}),
        name='task-detail',
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
    
    # Task Comments
    path(
        'tasks/allcomments/',
        CommentViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='all-comments',
    ),
    path(
        'tasks/<int:task_id>/comments/<int:pk>/',
        CommentViewSet.as_view({
            'get': 'retrieve',
            'patch': 'update',
            'delete': 'destroy',
        }),
        name='task-comment-detail',
    ),
]

