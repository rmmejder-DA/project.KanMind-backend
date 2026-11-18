"""Views for boards, tasks and task comments."""

from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_app.api.serializers import UserSerializer
from kanban_app.api.permissions import (
    IsBoardMember,
    IsBoardOwnerOrReadOnly,
    IsCommentAuthor,
    IsTaskCreatorOrBoardOwner,
)
from kanban_app.api.serializers import (
    BoardDetailSerializer,
    BoardListSerializer,
    BoardSerializer,
    BoardUpdateSerializer,
    CommentSerializer,
    TaskCommentSerializer,
    TaskSerializer,
)
from kanban_app.models import Board, Comment, Task


def parse_pk(value):
    """Return a URL ID as int. Malformed IDs give 400 instead of 404."""
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError("Invalid ID.")


class BoardViewSet(viewsets.ModelViewSet):
    """Boards the current user owns or is a member of."""

    queryset = Board.objects.all()
    serializer_class = BoardSerializer

    def get_permissions(self):
        """Members may update a board; only the owner may delete it."""
        if self.action == "destroy":
            return [
                IsAuthenticated(),
                IsBoardMember(),
                IsBoardOwnerOrReadOnly(),
            ]
        return [IsAuthenticated(), IsBoardMember()]

    def get_queryset(self):
        """Return the boards visible for the current action."""
        user = self.request.user
        if self.action == "retrieve":
            # Non-members get 403 from IsBoardMember instead of 404.
            tasks = Task.objects.annotate(comments_count=Count("comments"))
            return Board.objects.prefetch_related(
                Prefetch("tasks", queryset=tasks)
            )
        if self.action in ("update", "partial_update", "destroy"):
            return Board.objects.all()
        return Board.objects.filter(Q(members=user) | Q(owner=user)).distinct()

    def get_serializer_class(self):
        """Pick the serializer that matches the current action."""
        if self.action == "retrieve":
            return BoardDetailSerializer
        if self.action == "list":
            return BoardListSerializer
        return BoardSerializer

    def update(self, request, *args, **kwargs):
        """Update title and members and return the board with user data."""
        partial = kwargs.pop("partial", False)
        board = self.get_object()
        serializer = self.get_serializer(
            board, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(BoardUpdateSerializer(board).data)

    def create(self, request, *args, **kwargs):
        """Create a board and return its overview without the member list."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        board_data = BoardListSerializer(serializer.instance).data
        return Response(board_data, status=status.HTTP_201_CREATED)

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

    def get_permissions(self):
        """Only the task creator or the board owner may delete a task."""
        if self.action == "destroy":
            return [
                IsAuthenticated(),
                IsBoardMember(),
                IsTaskCreatorOrBoardOwner(),
            ]
        return [IsAuthenticated(), IsBoardMember()]

    def get_queryset(self):
        """Return all tasks, limited to the user's boards for the list."""
        queryset = Task.objects.annotate(comments_count=Count("comments"))
        if self.action == "list":
            return queryset.filter(board__members=self.request.user).distinct()
        return queryset

    def get_object(self):
        """Return the task after validating the ID in the URL."""
        self.kwargs["pk"] = parse_pk(self.kwargs["pk"])
        return super().get_object()

    def create(self, request, *args, **kwargs):
        """Create a task if the requesting user is a board member."""
        self.check_board_membership(request)
        return super().create(request, *args, **kwargs)

    def check_board_membership(self, request):
        """Raise 404 for an unknown board and 403 for a non-member."""
        board_id = request.data.get("board")
        if board_id is None:
            return
        try:
            board = Board.objects.get(pk=board_id)
        except (Board.DoesNotExist, ValueError, TypeError):
            raise NotFound("Board not found.")
        if not board.members.filter(pk=request.user.pk).exists():
            raise PermissionDenied(
                "You must be a board member to create tasks."
            )

    def perform_create(self, serializer):
        """Save the task with the requesting user as creator."""
        serializer.save(created_by=self.request.user)
        serializer.instance.comments_count = 0


class UserTaskListView(generics.ListAPIView):
    """Lists tasks linked to the current user through one relation."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    user_field = None

    def get_queryset(self):
        """Return the tasks linked to the user through user_field."""
        if not self.user_field:
            return Task.objects.none()

        return Task.objects.filter(
            **{self.user_field: self.request.user}
        ).annotate(comments_count=Count("comments"))


class AssignedTaskListView(UserTaskListView):
    """Tasks assigned to the current user."""

    user_field = "assignee"


class ReviewingTaskListView(UserTaskListView):
    """Lists tasks the current user is a reviewer of."""

    user_field = "reviewer"


class TaskCommentListView(generics.ListCreateAPIView):
    """Comments of one task, oldest first, for board members only."""

    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_task(self):
        """Return the task if the requesting user is a board member."""
        task = get_object_or_404(Task, pk=self.kwargs["task_id"])
        if not task.board.members.filter(pk=self.request.user.pk).exists():
            raise PermissionDenied(
                "You must be a board member to access these comments."
            )
        return task

    def get_queryset(self):
        """Return the comments of the task, oldest first."""
        return (
            self.get_task()
            .comments.select_related("author")
            .order_by("created_at", "id")
        )

    def create(self, request, *args, **kwargs):
        """Check access before validating the body so outsiders get 403."""
        self.task = self.get_task()
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Save the comment for the task and the requesting user."""
        serializer.save(task=self.task, author=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    """Comments on tasks the current user is a member of."""

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsBoardMember, IsCommentAuthor]

    def get_queryset(self):
        """Return the comments the requesting user may see."""
        queryset = Comment.objects.all()
        if self.action == "list":
            queryset = queryset.filter(task__board__members=self.request.user)
        if 'task_id' in self.kwargs:
            queryset = queryset.filter(task_id=self.kwargs['task_id'])
        return queryset

    def get_object(self):
        """Return the comment after validating the ID in the URL."""
        self.kwargs["pk"] = parse_pk(self.kwargs["pk"])
        return super().get_object()

    def perform_create(self, serializer):
        """Save the comment on the task given in the request body."""
        task = get_object_or_404(
            Task,
            pk=self.request.data.get('task'),
            board__members=self.request.user,
        )
        serializer.save(task=task, author=self.request.user)


class BoardMembersListView(generics.ListAPIView):
    """Members of a specific board the current user is a member of."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsBoardMember]

    def get_queryset(self):
        """Return the members of the board given in the URL."""
        board = get_object_or_404(
            Board,
            pk=self.kwargs["board_id"],
            members=self.request.user,
        )
        return board.members.all()
