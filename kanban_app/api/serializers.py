"""Serializers for boards, tasks and task comments."""

from rest_framework import serializers

from auth_app.api.serializers import UserSerializer
from auth_app.models import User
from kanban_app.models import Board, Comment, Task


def ensure_board_member(board, user):
    """Raise a validation error when the user is not a board member."""
    if not board.members.filter(pk=user.pk).exists():
        raise serializers.ValidationError("You are not a member of this board.")


class BoardSerializer(serializers.ModelSerializer):
    """Board overview with counters; members are written as user ids."""

    owner_id = serializers.IntegerField(read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False,
    )
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "owner_id",
            "members",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
        ]

    def validate_title(self, value):
        """Enforce the title length accepted by the frontend."""
        if not 2 < len(value.strip()) < 64:
            raise serializers.ValidationError(
                "Title must be between 3 and 63 characters."
            )
        return value.strip()

    def get_member_count(self, obj):
        """Return the number of members."""
        return obj.members.count()

    def get_ticket_count(self, obj):
        """Return the number of tasks on the board."""
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        """Return the number of tasks with the to-do status."""
        return obj.tasks.filter(status="to-do").count()

    def get_tasks_high_prio_count(self, obj):
        """Return the number of tasks with high priority."""
        return obj.tasks.filter(priority="high").count()


class TaskSerializer(serializers.ModelSerializer):
    """Task data including nested assignee and reviewer."""

    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)

    assignee_id = serializers.PrimaryKeyRelatedField(
        source="assignee",
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    reviewer_id = serializers.PrimaryKeyRelatedField(
        source="reviewer",
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "assignee_id",
            "reviewer",
            "reviewer_id",
            "due_date",
            "comments_count",
        ]

        extra_kwargs = {
            "board": {"required": False},
            "title": {"required": False},
        }

    def validate_board(self, board):
        """Allow only board members to create tasks."""
        ensure_board_member(
            board,
            self.context["request"].user,
        )
        return board

    def validate(self, attrs):
        """Ensure assignee and reviewer belong to the board."""

        board = attrs.get(
            "board",
            getattr(self.instance, "board", None),
        )

        if not board:
            return attrs

        assignee = attrs.get("assignee")
        reviewer = attrs.get("reviewer")

        if assignee:
            ensure_board_member(board, assignee)

        if reviewer:
            ensure_board_member(board, reviewer)

        return attrs

class BoardDetailSerializer(BoardSerializer):
    """Board with full member and task data for the board view."""

    members = UserSerializer(many=True, read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta(BoardSerializer.Meta):
        fields = BoardSerializer.Meta.fields + ["tasks"]


class CommentSerializer(serializers.ModelSerializer):
    """Comment data with the author's full name."""

    author = serializers.CharField(source="author.fullname", read_only=True)

    class Meta:
        model = Comment
        fields = ["author", "comment"]
