"""Views for boards, tasks and task comments."""

from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
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
from django.db.models import Count, Prefetch, Q


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
            return [IsAuthenticated(), IsBoardMember(), IsBoardOwnerOrReadOnly()]
        return [IsAuthenticated(), IsBoardMember()]

    def get_queryset(self):
        user = self.request.user
        if self.action == "retrieve":
            # Non-members get 403 from IsBoardMember instead of 404.
            tasks = Task.objects.annotate(comments_count=Count("comments"))
            return Board.objects.prefetch_related(Prefetch("tasks", queryset=tasks))
        if self.action in ("update", "partial_update", "destroy"):
            return Board.objects.all()
        return Board.objects.filter(Q(members=user) | Q(owner=user)).distinct()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BoardDetailSerializer
        if self.action == "list":
            return BoardListSerializer
        return BoardSerializer

    def update(self, request, *args, **kwargs):
        """Update title and members and return the board with user data."""
        partial = kwargs.pop("partial", False)
        board = self.get_object()
        serializer = self.get_serializer(board, data=request.data, partial=partial)
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
            return [IsAuthenticated(), IsBoardMember(), IsTaskCreatorOrBoardOwner()]
        return [IsAuthenticated(), IsBoardMember()]

    def get_queryset(self):
        queryset = Task.objects.annotate(comments_count=Count("comments"))
        if self.action == "list":
            return queryset.filter(board__members=self.request.user).distinct()
        return queryset

    def get_object(self):
        self.kwargs["pk"] = parse_pk(self.kwargs["pk"])
        return super().get_object()

    def create(self, request, *args, **kwargs):
        board_id = request.data.get("board")
        if board_id is not None:
            try:
                board = Board.objects.get(pk=board_id)
            except (Board.DoesNotExist, ValueError, TypeError):
                raise NotFound("Board not found.")
            if not board.members.filter(pk=request.user.pk).exists():
                raise PermissionDenied("You must be a board member to create tasks.")
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        serializer.instance.comments_count = 0

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
        ).annotate(comments_count=Count("comments"))


class AssignedTaskListView(UserTaskListView):
    """Tasks assigned to the current user."""

    user_field = "assignee"


class ReviewingTaskListView(UserTaskListView):
    user_field = "reviewer"
    

class TaskCommentListView(generics.ListCreateAPIView):
    """Comments of one task, oldest first. Only board members may read or write them."""

    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_task(self):
        task = get_object_or_404(Task, pk=self.kwargs["task_id"])
        if not task.board.members.filter(pk=self.request.user.pk).exists():
            raise PermissionDenied("You must be a board member to access these comments.")
        return task

    def get_queryset(self):
        return self.get_task().comments.select_related("author").order_by("created_at", "id")

    def create(self, request, *args, **kwargs):
        # Check task and membership before validating the body, so outsiders get 403 for any body.
        self.task = self.get_task()
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(task=self.task, author=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    """Comments on tasks the current user is a member of."""

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsBoardMember, IsCommentAuthor]

    def get_queryset(self):
        queryset = Comment.objects.all()
        if self.action == "list":
            queryset = queryset.filter(task__board__members=self.request.user)
        if 'task_id' in self.kwargs:
            queryset = queryset.filter(task_id=self.kwargs['task_id'])
        return queryset

    def get_object(self):
        self.kwargs["pk"] = parse_pk(self.kwargs["pk"])
        return super().get_object()

    def perform_create(self, serializer):
        """Attach the comment to the task given in the body and to the requesting user."""
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
        board = get_object_or_404(
            Board,
            pk=self.kwargs["board_id"],
            members=self.request.user,
        )
        return board.members.all()
