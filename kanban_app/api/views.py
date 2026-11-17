"""Views for boards, tasks and task comments."""

from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated

from auth_app.api.serializers import UserSerializer
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
from django.db.models import Count


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
        if self.action == "retrieve":
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

    queryset = Task.objects.annotate(comments_count=Count("comments"))
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
        if not self.user_field:
            return Task.objects.none()

        return Task.objects.filter(
            **{self.user_field: self.request.user}
        )


class AssignedTaskListView(UserTaskListView):
    """Tasks assigned to the current user."""

    user_field = "assignee"


class ReviewingTaskListView(UserTaskListView):
    user_field = "reviewer"
    

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


class BoardMembersListView(generics.ListAPIView):
    """Members of a specific board the current user is a member of."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsBoardMember]

    def get_queryset(self):
        board = get_object_or_404(
            Board,
            pk=self.kwargs["board_id"],
            members=self.request.user,
        )
        return board.members.all()
