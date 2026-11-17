"""Admin configuration for boards, tasks and comments."""

from django.contrib import admin

from kanban_app.models import Board, Comment, Task


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Manages boards and their members."""

    list_display = ['title', 'owner']
    search_fields = ['title']
    filter_horizontal = ['members']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Manages tasks with status and priority filters."""

    list_display = ['title', 'board', 'status', 'priority', 'due_date']
    list_filter = ['status', 'priority']
    search_fields = ['title']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Shows comments with their task and author."""

    list_display = ['task', 'author', 'comment']
