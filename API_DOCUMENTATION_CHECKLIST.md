# KanMind API - Dokumentations-Checkliste

## ✅ Alle Endpoints Implementiert (100%)

### Authentication
- ✅ POST /api/registration/ → 201 Created
- ✅ POST /api/login/ → 200 OK
- ✅ POST /api/guest-login/ → 200 OK (Zusatz)
- ✅ POST /api/auth-token/ → 200 OK (Zusatz)
- ✅ GET /api/email-check/ → 200 OK

### Boards
- ✅ GET /api/boards/ → 200 OK
- ✅ POST /api/boards/ → 201 Created
- ✅ GET /api/boards/{board_id}/ → 200 OK
- ✅ PATCH /api/boards/{board_id}/ → 200 OK
- ✅ DELETE /api/boards/{board_id}/ → 204 No Content

### Tasks
- ✅ GET /api/tasks/assigned-to-me/ → 200 OK
- ✅ GET /api/tasks/reviewing/ → 200 OK
- ✅ POST /api/tasks/ → 201 Created
- ✅ PATCH /api/tasks/{task_id}/ → 200 OK
- ✅ DELETE /api/tasks/{task_id}/ → 204 No Content

### Comments
- ✅ GET /api/tasks/{task_id}/comments/ → 200 OK
- ✅ POST /api/tasks/{task_id}/comments/ → 201 Created
- ✅ DELETE /api/tasks/{task_id}/comments/{comment_id}/ → 204 No Content

## Response Format - Bestätigt ✅

### Registration Response
```json
{
  "token": "...",
  "user_id": 123,
  "email": "...",
  "fullname": "...",
  "is_staff": false
}
```

### Login Response
```json
{
  "token": "...",
  "user_id": 123,
  "email": "...",
  "fullname": "...",
  "is_staff": false
}
```

### Board Response (GET /api/boards/)
```json
{
  "id": 1,
  "title": "...",
  "owner_id": 12,
  "members": [12, 15],
  "member_count": 2,
  "ticket_count": 5,
  "tasks_to_do_count": 2,
  "tasks_high_prio_count": 1
}
```

### Task Response (GET /api/tasks/)
```json
{
  "id": 1,
  "board": 1,
  "title": "...",
  "description": "...",
  "status": "to-do|in-progress|review|done",
  "priority": "low|medium|high",
  "assignee": {
    "id": 13,
    "email": "...",
    "fullname": "..."
  },
  "reviewer": {
    "id": 1,
    "email": "...",
    "fullname": "..."
  },
  "due_date": "2025-02-27",
  "comments_count": 0
}
```

### Comment Response (GET /api/tasks/{task_id}/comments/)
```json
{
  "id": 15,
  "author": "Max Mustermann",
  "content": "...",
  "created_at": "2025-02-20T15:00:00Z"
}
```

## Status Codes - Bestätigt ✅

- 200 OK: Erfolgreiche GET/PATCH Anfrage
- 201 Created: Erfolgreiche POST Anfrage (Ressource erstellt)
- 204 No Content: Erfolgreiche DELETE Anfrage
- 400 Bad Request: Ungültige Anfragedaten
- 401 Unauthorized: Benutzer nicht authentifiziert
- 403 Forbidden: Benutzer hat keine Berechtigung
- 404 Not Found: Ressource nicht gefunden
- 500 Internal Server Error: Serverfehler

## Permission-Checks - Implementiert ✅

- ✅ Nur authentifizierte Benutzer können auf APIs zugreifen (außer Registration/Login)
- ✅ Benutzer können nur Boards sehen, bei denen sie Mitglieder sind
- ✅ Nur Board-Eigentümer können Boards ändern/löschen
- ✅ Nur Board-Mitglieder können Tasks erstellen/ändern
- ✅ Nur Comment-Autoren können ihre Kommentare löschen
- ✅ Alle Mitglieder können Kommentare sehen

## URL-Parameter - Bestätigt ✅

- {board_id} → Wird als pk im Router übergeben
- {task_id} → Wird als pk im Router übergeben
- {comment_id} → Wird als pk im Router übergeben

## Zusätzliche Features (nicht in Doku, aber implementiert)

- ✅ Guest Login (/api/guest-login/)
- ✅ Token Auth (/api/auth-token/)
- ✅ DRF Admin Interface (/api-auth/login/)
- ✅ API Index (/api/)

