"""URL routes for boards, tasks and task comments."""

from django.urls import path

from kanban_app.api.views import (
    AssignedTaskListView,
    BoardMembersListView,
    BoardViewSet,
    CommentViewSet,
    ReviewingTaskListView,
    TaskCommentListView,
    TaskViewSet,
)

urlpatterns = [
    # Boards
    path(
        "boards/",
        BoardViewSet.as_view({"get": "list", "post": "create"}),
        name="board-list",
    ),
    path(
        "boards/<int:pk>/",
        BoardViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="board-detail",
    ),
    path(
        "boards/<int:board_id>/members/",
        BoardMembersListView.as_view(),
        name="board-members",
    ),
    # Tasks
    path(
        "tasks/",
        TaskViewSet.as_view({"get": "list", "post": "create"}),
        name="task-list",
    ),
    path(
        "tasks/assigned-to-me/",
        AssignedTaskListView.as_view(),
        name="tasks-assigned",
    ),
    path(
        "tasks/reviewing/",
        ReviewingTaskListView.as_view(),
        name="tasks-reviewing",
    ),
    # Task Comments
    path(
        "tasks/<int:task_id>/comments/",
        TaskCommentListView.as_view(),
        name="task-comments",
    ),
    path(
        "tasks/allcomments/",
        CommentViewSet.as_view({"get": "list", "post": "create"}),
        name="all-comments",
    ),
    path(
        "tasks/<int:task_id>/comments/<str:pk>/",
        CommentViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="task-comment-detail",
    ),
    # Must come after the fixed task paths above, since <str:pk> matches
    # them too.
    path(
        "tasks/<str:pk>/",
        TaskViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="task-detail",
    ),
]
