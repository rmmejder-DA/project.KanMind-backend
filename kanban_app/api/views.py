"""Views for boards, tasks and task comments."""

from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated

from kanban_app.api.permissions import (
    IsBoardMember,
    IsBoardOwnerOrReadOnly,
    IsCommentAuthor,
)
from kanban_app.api.serializers import (
    BoardDetailSerializer,
    BoardSerializer,
    CommentSerializer,
    TaskSerializer,
)
from kanban_app.models import Board, Comment, Task


class BoardViewSet(viewsets.ModelViewSet):
    """Boards the current user is a member of."""

    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [
        IsAuthenticated,
        IsBoardMember,
        IsBoardOwnerOrReadOnly,
    ]

    def get_queryset(self):
        return Board.objects.filter(members=self.request.user).distinct()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BoardDetailSerializer
        return BoardSerializer

    def perform_create(self, serializer):
        """Make the requesting user the owner and a member."""
        board = serializer.save(owner=self.request.user)
        board.members.add(self.request.user)

    def perform_update(self, serializer):
        """Keep the owner in the member list when members change."""
        board = serializer.save()
        board.members.add(board.owner)


class TaskViewSet(viewsets.ModelViewSet):
    """Tasks on boards the current user is a member of."""

    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsBoardMember]

    def get_queryset(self):
        return Task.objects.filter(board__members=self.request.user).distinct()


class UserTaskListView(generics.ListAPIView):
    """Lists tasks linked to the current user through one relation."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    user_field = None

    def get_queryset(self):
        return Task.objects.filter(**{self.user_field: self.request.user})


class AssignedTaskListView(UserTaskListView):
    """Tasks assigned to the current user."""

    user_field = 'assignee'


class ReviewingTaskListView(UserTaskListView):
    """Tasks the current user has to review."""

    user_field = 'reviewer'


class CommentViewSet(viewsets.ModelViewSet):
    """Comments on a task the current user has access to."""

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsBoardMember, IsCommentAuthor]

    def get_queryset(self):
        return Comment.objects.filter(
            task_id=self.kwargs['task_id'],
            task__board__members=self.request.user,
        )

    def perform_create(self, serializer):
        """Attach the comment to the task and to the requesting user."""
        task = get_object_or_404(
            Task,
            pk=self.kwargs['task_id'],
            board__members=self.request.user,
        )
        serializer.save(task=task, author=self.request.user)
