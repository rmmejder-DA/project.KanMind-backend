"""Permission classes for board, task and comment endpoints."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from kanban_app.models import Board, Comment


def get_board(obj):
    """Return the board that a board, task or comment belongs to."""
    if isinstance(obj, Board):
        return obj
    if isinstance(obj, Comment):
        return obj.task.board
    return obj.board


class IsBoardMember(BasePermission):
    """Allows access only to members of the object's board."""

    def has_object_permission(self, request, view, obj):
        return get_board(obj).members.filter(pk=request.user.pk).exists()


class IsBoardOwnerOrReadOnly(BasePermission):
    """Allows only the board owner to change the board."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.owner_id == request.user.pk
        )


class IsCommentAuthor(BasePermission):
    """Allows only the author of a comment to delete it."""

    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.pk
