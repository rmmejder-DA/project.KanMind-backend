"""Tests for the board, task and comment endpoints."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from kanban_app.models import Board, Comment, Task

User = get_user_model()

BOARDS_URL = '/api/boards/'
TASKS_URL = '/api/tasks/'
ASSIGNED_URL = '/api/tasks/assigned-to-me/'
REVIEWING_URL = '/api/tasks/reviewing/'
ALL_COMMENTS_URL = '/api/tasks/allcomments/'


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
            reviewer=self.owner, created_by=self.owner,
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

        self.assertEqual(response.status_code, 403)

    def test_member_can_update_board_members(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.patch(
            f'{BOARDS_URL}{self.board.id}/',
            {'title': 'Neu', 'members': [self.member.pk]},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Neu')
        self.assertEqual(response.data['owner_data']['id'], self.owner.pk)
        member_ids = {user['id'] for user in response.data['members_data']}
        self.assertEqual(member_ids, {self.owner.pk, self.member.pk})

    def test_owner_can_delete_board(self):
        response = self.client.delete(f'{BOARDS_URL}{self.board.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Board.objects.filter(pk=self.board.pk).exists())

    def test_member_cannot_delete_board(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.delete(f'{BOARDS_URL}{self.board.id}/')

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Board.objects.filter(pk=self.board.pk).exists())

    def test_task_on_foreign_board_is_forbidden(self):
        other_board = Board.objects.create(title='Fremd', owner=self.outsider)

        response = self.client.post(TASKS_URL, {
            'board': other_board.id, 'title': 'Hack',
            'status': 'to-do', 'priority': 'low',
        }, format='json')

        self.assertEqual(response.status_code, 403)

    def test_create_task_returns_created_task(self):
        response = self.client.post(TASKS_URL, {
            'board': self.board.id, 'title': 'Code-Review durchführen',
            'description': 'PR prüfen', 'status': 'review',
            'priority': 'medium', 'assignee_id': self.member.id,
            'reviewer_id': self.owner.id, 'due_date': '2025-02-27',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['board'], self.board.id)
        self.assertEqual(response.data['assignee']['id'], self.member.id)
        self.assertEqual(response.data['reviewer']['id'], self.owner.id)
        self.assertEqual(response.data['comments_count'], 0)
        self.assertEqual(
            Task.objects.get(pk=response.data['id']).created_by, self.owner,
        )

    def test_create_task_with_non_member_assignee_is_rejected(self):
        response = self.client.post(TASKS_URL, {
            'board': self.board.id, 'title': 'Aufgabe',
            'assignee_id': self.outsider.id,
        }, format='json')

        self.assertEqual(response.status_code, 400)

    def test_create_task_on_unknown_board_returns_404(self):
        response = self.client.post(TASKS_URL, {
            'board': 99999, 'title': 'Aufgabe',
        }, format='json')

        self.assertEqual(response.status_code, 404)

    def test_member_can_update_task(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.patch(f'{TASKS_URL}{self.task.id}/', {
            'title': 'Code-Review abschließen', 'status': 'done',
            'priority': 'high', 'assignee_id': self.owner.id,
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Code-Review abschließen')
        self.assertEqual(response.data['assignee']['id'], self.owner.id)
        self.assertIn('comments_count', response.data)

    def test_outsider_cannot_update_task(self):
        self.client.force_authenticate(user=self.outsider)

        response = self.client.patch(f'{TASKS_URL}{self.task.id}/', {
            'title': 'Hack',
        }, format='json')

        self.assertEqual(response.status_code, 403)

    def test_task_board_cannot_be_changed(self):
        other_board = Board.objects.create(title='Anderes', owner=self.owner)
        other_board.members.add(self.owner)

        response = self.client.patch(f'{TASKS_URL}{self.task.id}/', {
            'board': other_board.id,
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.task.refresh_from_db()
        self.assertEqual(self.task.board, self.board)

    def test_update_unknown_task_returns_404(self):
        response = self.client.patch(f'{TASKS_URL}99999/', {
            'title': 'Aufgabe',
        }, format='json')

        self.assertEqual(response.status_code, 404)

    def test_task_creator_can_delete_task(self):
        task = Task.objects.create(
            board=self.board, title='Eigene', created_by=self.member,
        )
        self.client.force_authenticate(user=self.member)

        response = self.client.delete(f'{TASKS_URL}{task.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_member_cannot_delete_task_of_other_creator(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.delete(f'{TASKS_URL}{self.task.id}/')

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

    def test_delete_task_with_malformed_id_returns_400(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(f'{TASKS_URL}abc/')

        self.assertEqual(response.status_code, 400)
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

    def test_board_owner_can_delete_any_task(self):
        task = Task.objects.create(
            board=self.board, title='Fremd', created_by=self.member,
        )

        response = self.client.delete(f'{TASKS_URL}{task.id}/')

        self.assertEqual(response.status_code, 204)

    def test_anonymous_request_gets_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(REVIEWING_URL)

        self.assertEqual(response.status_code, 401)

    def test_assigned_and_reviewing_lists(self):
        self.client.force_authenticate(user=self.owner)
        reviewing = self.client.get(REVIEWING_URL)
        self.assertEqual(len(reviewing.data), 1)
        self.assertIn('comments_count', reviewing.data[0])

        self.client.force_authenticate(user=self.member)
        assigned = self.client.get(ASSIGNED_URL)
        self.assertEqual(len(assigned.data), 1)
        self.assertIn('comments_count', assigned.data[0])

    def test_comment_create_list_and_delete(self):
        self.client.force_authenticate(user=self.member)
        created = self.client.post(
            ALL_COMMENTS_URL,
            {'task': self.task.id, 'comment': 'Hallo'},
            format='json',
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data['author'], 'Mia Member')

        listed = self.client.get(ALL_COMMENTS_URL)
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

    def test_comment_delete_by_outsider_is_forbidden(self):
        comment = Comment.objects.create(
            task=self.task, author=self.member, comment='Meins',
        )
        self.client.force_authenticate(user=self.outsider)

        response = self.client.delete(
            f'{comments_url(self.task.id)}{comment.id}/',
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    def test_comment_delete_unknown_or_on_other_task_returns_404(self):
        other_task = Task.objects.create(board=self.board, title='Andere')
        comment = Comment.objects.create(
            task=self.task, author=self.owner, comment='Hier',
        )

        unknown = self.client.delete(f'{comments_url(self.task.id)}9999/')
        wrong_task = self.client.delete(f'{comments_url(other_task.id)}{comment.id}/')

        self.assertEqual(unknown.status_code, 404)
        self.assertEqual(wrong_task.status_code, 404)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    def test_outsider_cannot_comment(self):
        self.client.force_authenticate(user=self.outsider)

        response = self.client.post(
            ALL_COMMENTS_URL,
            {'task': self.task.id, 'comment': 'Hi'},
            format='json',
        )

        self.assertEqual(response.status_code, 404)

    def test_task_comments_are_sorted_oldest_first_with_content(self):
        newer = Comment.objects.create(
            task=self.task, author=self.member, comment='Eins',
        )
        older = Comment.objects.create(
            task=self.task, author=self.owner, comment='Zwei',
        )
        Comment.objects.filter(pk=older.pk).update(
            created_at=timezone.now() - timedelta(days=1),
        )

        response = self.client.get(comments_url(self.task.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual([c['id'] for c in response.data], [older.id, newer.id])
        self.assertEqual(
            set(response.data[0]), {'id', 'created_at', 'author', 'content'},
        )
        self.assertEqual(response.data[0]['author'], 'Olga Owner')
        self.assertEqual(response.data[0]['content'], 'Zwei')

    def test_task_comments_forbidden_for_non_member(self):
        self.client.force_authenticate(user=self.outsider)

        response = self.client.get(comments_url(self.task.id))

        self.assertEqual(response.status_code, 403)

    def test_task_comments_unknown_task_returns_404(self):
        response = self.client.get(comments_url(9999))

        self.assertEqual(response.status_code, 404)

    def test_task_comment_create_returns_content_and_author(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.post(
            comments_url(self.task.id), {'content': 'Neu'}, format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['content'], 'Neu')
        self.assertEqual(response.data['author'], 'Mia Member')
        self.assertTrue(
            Comment.objects.filter(task=self.task, author=self.member, comment='Neu').exists()
        )

    def test_task_comment_create_rejects_empty_content(self):
        response = self.client.post(
            comments_url(self.task.id), {'content': '   '}, format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Comment.objects.exists())

    def test_task_comment_create_forbidden_for_non_member(self):
        self.client.force_authenticate(user=self.outsider)

        response = self.client.post(
            comments_url(self.task.id), {'content': 'Hi'}, format='json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Comment.objects.exists())
