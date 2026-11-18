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
    """Allows access only to members or the owner of the object's board."""

    def has_object_permission(self, request, view, obj):
        """Allow the request if the user is a member or the owner."""
        board = get_board(obj)
        return (
            board.members.filter(pk=request.user.pk).exists()
            or board.owner_id == request.user.pk
        )


class IsBoardOwnerOrReadOnly(BasePermission):
    """Allows only the board owner to change the board."""

    def has_object_permission(self, request, view, obj):
        """Allow safe methods for everyone and writes for the owner."""
        return (
            request.method in SAFE_METHODS
            or obj.owner_id == request.user.pk
        )


class IsTaskCreatorOrBoardOwner(BasePermission):
    """Allows deleting a task only for its creator or the board owner."""

    def has_object_permission(self, request, view, obj):
        """Allow the task creator or the board owner."""
        return (
            obj.created_by_id == request.user.pk
            or obj.board.owner_id == request.user.pk
        )


class IsCommentAuthor(BasePermission):
    """Allows only the author to delete a comment; all members can read."""

    def has_object_permission(self, request, view, obj):
        """Allow reads for everyone and deletes for the author."""
        if request.method in SAFE_METHODS:
            return True
        return obj.author_id == request.user.pk
