# KanMind API - Komplette Dokumentation

## Base URL
```
http://127.0.0.1:8000
```

## Authentication
Alle Requests außer Registration und Login erfordern das Bearer Token:
```
Authorization: Token <YOUR_TOKEN>
```

---

## 1. Authentication (Auth)

### 1.1 User Registration
```
POST /api/registration/
```

**Request Body:**
```json
{
  "fullname": "Example Username",
  "email": "example@mail.de",
  "password": "examplePassword",
  "repeated_password": "examplePassword"
}
```

**Success Response (201 Created):**
```json
{
  "token": "83bf098723b08f7b23429u0fv8274",
  "user_id": 123,
  "email": "example@mail.de",
  "fullname": "Example Username",
  "is_staff": false
}
```

---

### 1.2 User Login
```
POST /api/login/
```

**Request Body:**
```json
{
  "email": "example@mail.de",
  "password": "examplePassword"
}
```

**Success Response (200 OK):**
```json
{
  "token": "83bf098723b08f7b23429u0fv8274",
  "user_id": 123,
  "email": "example@mail.de",
  "fullname": "Example Username",
  "is_staff": false
}
```

---

### 1.3 Guest Login
```
POST /api/guest-login/
```

**Success Response (200 OK):**
```json
{
  "mode": "guest",
  "message": "Guest mode enabled",
  "token": null,
  "user_id": null,
  "email": "guest@example.com",
  "fullname": "Guest User"
}
```

---

### 1.4 Email Check
```
GET /api/email-check/?email=user@example.com
```

**Success Response (200 OK):**
```json
{
  "id": 123,
  "email": "user@example.com",
  "fullname": "Example User"
}
```

**Requires:** Authentication ✅

---

## 2. Boards

### 2.1 List All Boards
```
GET /api/boards/
```

**Success Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Projekt X",
    "owner_id": 12,
    "members": [12, 15, 18],
    "member_count": 2,
    "ticket_count": 5,
    "tasks_to_do_count": 2,
    "tasks_high_prio_count": 1
  },
  {
    "id": 2,
    "title": "Projekt Y",
    "owner_id": 3,
    "members": [3, 12, 15],
    "member_count": 3,
    "ticket_count": 43,
    "tasks_to_do_count": 12,
    "tasks_high_prio_count": 5
  }
]
```

**Requires:** Authentication ✅

---

### 2.2 Create Board
```
POST /api/boards/
```

**Request Body:**
```json
{
  "title": "Mein neues Board"
}
```

**Success Response (201 Created):**
```json
{
  "id": 5,
  "title": "Mein neues Board",
  "owner_id": 123,
  "members": [123],
  "member_count": 1,
  "ticket_count": 0,
  "tasks_to_do_count": 0,
  "tasks_high_prio_count": 0
}
```

**Requires:** Authentication ✅

---

### 2.3 Get Board Detail
```
GET /api/boards/{board_id}/
```

**Success Response (200 OK):**
```json
{
  "id": 1,
  "title": "Projekt X",
  "owner_id": 12,
  "members": [
    {
      "id": 12,
      "email": "max@example.com",
      "fullname": "Max Mustermann"
    },
    {
      "id": 15,
      "email": "marie@example.com",
      "fullname": "Marie Musterfrau"
    }
  ],
  "tasks": [
    {
      "id": 1,
      "board": 1,
      "title": "Feature X implementieren",
      "description": "...",
      "status": "in-progress",
      "priority": "high",
      "assignee": {
        "id": 12,
        "email": "max@example.com",
        "fullname": "Max Mustermann"
      },
      "reviewer": null,
      "due_date": "2025-02-27",
      "comments_count": 2
    }
  ]
}
```

**Requires:** Authentication ✅

---

### 2.4 Update Board
```
PATCH /api/boards/{board_id}/
```

**Request Body:**
```json
{
  "title": "Neuer Titel",
  "members": [12, 15, 18]
}
```

**Success Response (200 OK):**
```json
{
  "id": 1,
  "title": "Neuer Titel",
  "owner_id": 12,
  "members": [12, 15, 18],
  "member_count": 3,
  "ticket_count": 5,
  "tasks_to_do_count": 2,
  "tasks_high_prio_count": 1
}
```

**Requires:** Authentication ✅ + Board Owner

---

### 2.5 Delete Board
```
DELETE /api/boards/{board_id}/
```

**Success Response (204 No Content)**

**Requires:** Authentication ✅ + Board Owner

---

## 3. Tasks

### 3.1 List Tasks Assigned to Me
```
GET /api/tasks/assigned-to-me/
```

**Success Response (200 OK):**
```json
[
  {
    "id": 1,
    "board": 1,
    "title": "Feature X implementieren",
    "description": "...",
    "status": "in-progress",
    "priority": "high",
    "assignee": {
      "id": 12,
      "email": "max@example.com",
      "fullname": "Max Mustermann"
    },
    "reviewer": null,
    "due_date": "2025-02-27",
    "comments_count": 2
  }
]
```

**Requires:** Authentication ✅

---

### 3.2 List Tasks for Review
```
GET /api/tasks/reviewing/
```

**Success Response (200 OK):** (gleiches Format wie 3.1)

**Requires:** Authentication ✅

---

### 3.3 Create Task
```
POST /api/tasks/
```

**Request Body:**
```json
{
  "board": 12,
  "title": "Code-Review durchführen",
  "description": "Den neuen PR für das Feature X überprüfen",
  "status": "review",
  "priority": "medium",
  "assignee_id": 13,
  "reviewer_id": 1,
  "due_date": "2025-02-27"
}
```

**Status Values:** `to-do`, `in-progress`, `review`, `done`
**Priority Values:** `low`, `medium`, `high`

**Success Response (201 Created):**
```json
{
  "id": 10,
  "board": 12,
  "title": "Code-Review durchführen",
  "description": "Den neuen PR für das Feature X überprüfen",
  "status": "review",
  "priority": "medium",
  "assignee": {
    "id": 13,
    "email": "marie@example.com",
    "fullname": "Marie Musterfrau"
  },
  "reviewer": {
    "id": 1,
    "email": "max@example.com",
    "fullname": "Max Mustermann"
  },
  "due_date": "2025-02-27",
  "comments_count": 0
}
```

**Requires:** Authentication ✅ + Board Member

---

### 3.4 Update Task
```
PATCH /api/tasks/{task_id}/
```

**Request Body:** (beliebige Felder)
```json
{
  "status": "done",
  "priority": "low",
  "assignee_id": null
}
```

**Success Response (200 OK):** (gleiches Format wie 3.3)

**Requires:** Authentication ✅ + Board Member

---

### 3.5 Delete Task
```
DELETE /api/tasks/{task_id}/
```

**Success Response (204 No Content)**

**Requires:** Authentication ✅ + Board Member

---

## 4. Comments

### 4.1 List Comments on Task
```
GET /api/tasks/{task_id}/comments/
```

**Success Response (200 OK):**
```json
[
  {
    "id": 15,
    "author": "Max Mustermann",
    "content": "Das ist ein Kommentar zur Task.",
    "created_at": "2025-02-20T15:00:00Z"
  },
  {
    "id": 16,
    "author": "Marie Musterfrau",
    "content": "Ich stimme zu!",
    "created_at": "2025-02-20T15:05:00Z"
  }
]
```

**Requires:** Authentication ✅ + Board Member

---

### 4.2 Create Comment
```
POST /api/tasks/{task_id}/comments/
```

**Request Body:**
```json
{
  "content": "Das ist ein neuer Kommentar zur Task."
}
```

**Success Response (201 Created):**
```json
{
  "id": 15,
  "author": "Max Mustermann",
  "content": "Das ist ein neuer Kommentar zur Task.",
  "created_at": "2025-02-20T15:00:00Z"
}
```

**Requires:** Authentication ✅ + Board Member

---

### 4.3 Delete Comment
```
DELETE /api/tasks/{task_id}/comments/{comment_id}/
```

**Success Response (204 No Content)**

**Requires:** Authentication ✅ + Comment Author

---

## Status Codes Reference

| Code | Bedeutung |
|------|-----------|
| 200 | OK - Anfrage erfolgreich |
| 201 | Created - Ressource erfolgreich erstellt |
| 204 | No Content - Erfolg, aber keine Rückmeldung |
| 400 | Bad Request - Ungültige Anfragedaten |
| 401 | Unauthorized - Authentifizierung erforderlich |
| 403 | Forbidden - Keine Berechtigung |
| 404 | Not Found - Ressource nicht gefunden |
| 500 | Internal Server Error - Serverfehler |

---

## Error Response Format

```json
{
  "field_name": ["Error message 1", "Error message 2"],
  "other_field": ["Error message"]
}
```

oder für allgemeine Fehler:

```json
{
  "detail": "Error message"
}
```

---

## Testing mit cURL

### Login:
```bash
curl -X POST http://127.0.0.1:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"kevin@kovacsi.de","password":"asdasdasd"}'
```

### Get Boards:
```bash
curl -X GET http://127.0.0.1:8000/api/boards/ \
  -H "Authorization: Token YOUR_TOKEN"
```

### Create Task:
```bash
curl -X POST http://127.0.0.1:8000/api/tasks/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "board": 5,
    "title": "My Task",
    "status": "to-do",
    "priority": "high"
  }'
```

---

## Implementierungsstatus

✅ Alle Endpoints sind vollständig implementiert und getestet!
✅ Alle Response-Formate entsprechen der Dokumentation
✅ Alle Permission-Checks sind implementiert
✅ Alle Status Codes sind korrekt
