"""Tests for the board, task and comment endpoints."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from kanban_app.models import Board, Comment, Task

User = get_user_model()

BOARDS_URL = '/api/boards/'
TASKS_URL = '/api/tasks/'
ASSIGNED_URL = '/api/tasks/assigned-to-me/'
REVIEWING_URL = '/api/tasks/reviewing/'


def comments_url(task_id):
    return f'/api/tasks/{task_id}/comments/'


class KanbanApiTests(TestCase):
    """Covers board, task and comment permissions and behaviour."""

    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email='owner@example.com', password='pw12345678',
            fullname='Olga Owner',
        )
        self.member = User.objects.create_user(
            email='member@example.com', password='pw12345678',
            fullname='Mia Member',
        )
        self.outsider = User.objects.create_user(
            email='out@example.com', password='pw12345678',
            fullname='Oscar Outsider',
        )
        self.board = Board.objects.create(title='Projekt', owner=self.owner)
        self.board.members.add(self.owner, self.member)
        self.task = Task.objects.create(
            board=self.board, title='Aufgabe', assignee=self.member,
            reviewer=self.owner,
        )
        self.client.force_authenticate(user=self.owner)

    def test_create_board_adds_owner_as_member(self):
        response = self.client.post(BOARDS_URL, {
            'title': 'Neues Board', 'members': [self.member.id],
        }, format='json')

        self.assertEqual(response.status_code, 201)
        board = Board.objects.get(pk=response.data['id'])
        self.assertEqual(board.owner, self.owner)
        self.assertTrue(board.members.filter(pk=self.owner.pk).exists())

    def test_board_detail_contains_members_and_tasks(self):
        response = self.client.get(f'{BOARDS_URL}{self.board.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['members']), 2)
        self.assertEqual(len(response.data['tasks']), 1)

    def test_non_member_cannot_see_board(self):
        self.client.force_authenticate(user=self.outsider)

        response = self.client.get(f'{BOARDS_URL}{self.board.id}/')

        self.assertEqual(response.status_code, 404)

    def test_member_cannot_update_board(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.patch(
            f'{BOARDS_URL}{self.board.id}/', {'title': 'Neu'}, format='json',
        )

        self.assertEqual(response.status_code, 403)

    def test_owner_can_delete_board(self):
        response = self.client.delete(f'{BOARDS_URL}{self.board.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Board.objects.filter(pk=self.board.pk).exists())

    def test_task_on_foreign_board_is_rejected(self):
        other_board = Board.objects.create(title='Fremd', owner=self.outsider)

        response = self.client.post(TASKS_URL, {
            'board': other_board.id, 'title': 'Hack',
            'status': 'to-do', 'priority': 'low',
        }, format='json')

        self.assertEqual(response.status_code, 400)

    def test_assigned_and_reviewing_lists(self):
        self.client.force_authenticate(user=self.owner)
        reviewing = self.client.get(REVIEWING_URL)
        self.assertEqual(len(reviewing.data), 1)

        self.client.force_authenticate(user=self.member)
        assigned = self.client.get(ASSIGNED_URL)
        self.assertEqual(len(assigned.data), 1)

    def test_comment_create_list_and_delete(self):
        self.client.force_authenticate(user=self.member)
        created = self.client.post(
            comments_url(self.task.id), {'comment': 'Hallo'}, format='json',
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data['author'], 'Mia Member')

        listed = self.client.get(comments_url(self.task.id))
        self.assertEqual(len(listed.data), 1)

        comment_id = created.data['id']
        deleted = self.client.delete(
            f'{comments_url(self.task.id)}{comment_id}/',
        )
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(Comment.objects.exists())

    def test_comment_delete_by_non_author_is_forbidden(self):
        comment = Comment.objects.create(
            task=self.task, author=self.member, comment='Meins',
        )

        response = self.client.delete(
            f'{comments_url(self.task.id)}{comment.id}/',
        )

        self.assertEqual(response.status_code, 403)

    def test_outsider_cannot_comment(self):
        self.client.force_authenticate(user=self.outsider)

        response = self.client.post(
            comments_url(self.task.id), {'comment': 'Hi'}, format='json',
        )

        self.assertEqual(response.status_code, 404)
