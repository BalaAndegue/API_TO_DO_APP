# Collaborative Workspace API

> A professional **Trello-like** REST API built with Django 5 & Django REST Framework.  
> Boards · Lists · Cards · Checklists · Labels · Comments · Attachments · Real-time Activity Feed · Role-based Access Control

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Data Model](#data-model)
- [API Reference](#api-reference)
- [Authentication](#authentication)
- [Role-based Permissions](#role-based-permissions)
- [Query Filters](#query-filters)
- [Activity Feed](#activity-feed)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Frontend Integration Guide](#frontend-integration-guide)
- [Roadmap](#roadmap)

---

## Overview

This backend powers a collaborative task management workspace inspired by Trello. Multiple users can share **Boards**, organise work into **Lists** and **Cards**, assign team members, track progress with **Checklists**, and see a live **Activity Feed** of every action.

### Core Features

| Feature | Description |
|---|---|
| **Boards** | Workspaces with `public / private / workspace` visibility |
| **Lists** | Ordered columns inside a board (To-do, In Progress, Done…) |
| **Cards** | Tasks with title, description, due dates, cover image, archive |
| **Labels** | Colour-coded tags scoped to a board, attachable to cards |
| **Checklists** | Sub-task lists inside a card with progress tracking |
| **Comments** | Threaded discussion per card; author or admin can edit/delete |
| **Attachments** | File metadata linked to cards with uploader info |
| **Members** | Board-level roles (admin / member / observer) |
| **Card Assignments** | Assign specific board members to individual cards |
| **Invitations** | Email-based board invitations with secure UUID tokens |
| **Activity Feed** | Auto-logged audit trail for every significant action |
| **Search** | Card full-text search on title + description |
| **Pagination** | All list endpoints return paginated results (20/page) |

---

## Architecture

```
API_TO_DO_APP/
├── AuthenticationProject/       # Django project settings & root URLs
│   ├── settings.py              # Environment-aware configuration
│   └── urls.py                  # Swagger + API + frontend routes
│
├── Core/                        # Main application
│   ├── models.py                # 14 database models
│   ├── serializers.py           # Layered serializers (light / detail)
│   ├── permissions.py           # Custom permission classes
│   ├── signals.py               # Auto-logging activity feed
│   ├── utils.py                 # Custom exception handler
│   ├── apps.py                  # App config & signal registration
│   │
│   ├── ViewSet/                 # One ViewSet per resource
│   │   ├── UserViewSet.py       # Auth + user profile
│   │   ├── BoardViewSet.py      # Board CRUD + invite/close/reopen
│   │   ├── ListViewSet.py       # List CRUD + filtering
│   │   ├── CardViewSet.py       # Card CRUD + move/archive
│   │   ├── LabelViewSet.py
│   │   ├── ChecklistViewSet.py
│   │   ├── ChecklistItemViewSet.py
│   │   ├── CommentViewSet.py
│   │   ├── AttachmentViewSet.py
│   │   ├── CardMemberViewSet.py
│   │   ├── CardLabelViewSet.py
│   │   ├── BoardMemberViewSet.py
│   │   ├── ActivityViewSet.py   # Read-only feed
│   │   └── BoardInvitationViewSet.py
│   │
│   ├── urls_api.py              # /api/* router
│   └── urls_frontend.py         # Django template routes
│
├── templates/                   # Django HTML templates (optional UI)
├── static/                      # Static assets
├── requirements.txt
└── README.md
```

**Technology stack:** Django 5.2 · Django REST Framework 3.16 · SQLite (dev) / PostgreSQL (prod) · drf-yasg (Swagger) · django-cors-headers · Token Authentication

---

## Data Model

```
User
 └── Board (creator)
      ├── BoardMember (user → role: admin | member | observer)
      ├── BoardInvitation (email + UUID token)
      ├── Label (color tags scoped to board)
      ├── Activity (audit log)
      └── List (ordered columns)
           └── Card
                ├── CardMember (assigned users)
                ├── CardLabel (label associations)
                ├── Checklist
                │    └── ChecklistItem (checked / unchecked)
                ├── Comment
                └── Attachment
```

### Key Constraints

- A user can be a member of multiple boards with different roles.
- A card belongs to exactly one list and one board (denormalized for performance).
- Labels are board-scoped — only labels from the same board can be attached to its cards.
- An invitation token can only be accepted once (`accepted=False` gate + atomic transaction).
- Deleting a board cascades to all its lists, cards, and related objects.

---

## API Reference

Base URL: `http://localhost:8000/api/`  
Interactive docs: `http://localhost:8000/swagger/`  
ReDoc: `http://localhost:8000/redoc/`

### Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/register/` | None | Create account, returns token |
| POST | `/login/` | None | Sign in, returns token |
| POST | `/logout/` | Token | Invalidate current token |
| GET | `/users/me/` | Token | Get own profile |
| PATCH | `/users/{id}/` | Token (owner) | Update own profile |
| POST | `/users/change_password/` | Token | Change own password (rotates token) |

### Boards

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/boards/` | Token | List accessible boards (paginated) |
| POST | `/boards/` | Token | Create a board (auto-joined as admin) |
| GET | `/boards/{id}/` | Token | Board detail with lists summary + members |
| PATCH | `/boards/{id}/` | Token | Update board metadata |
| DELETE | `/boards/{id}/` | Token (admin) | Delete board |
| POST | `/boards/{id}/invite/` | Token (admin) | Invite user by email |
| GET | `/boards/{id}/members/` | Token | List board members |
| POST | `/boards/{id}/close/` | Token (admin) | Archive board |
| POST | `/boards/{id}/reopen/` | Token (admin) | Reopen archived board |

**Query params:** `?is_closed=true|false` · `?visibility=public|private|workspace`

### Lists

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/lists/` | Token | All accessible lists |
| POST | `/lists/` | Token (member) | Create list in a board |
| GET | `/lists/{id}/` | Token | List detail with cards |
| PATCH | `/lists/{id}/` | Token (member) | Rename or reorder |
| DELETE | `/lists/{id}/` | Token (admin) | Delete list (cascades cards) |

**Query params:** `?board=<id>` · `?archived=true|false`

### Cards

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/cards/` | Token | All accessible cards |
| POST | `/cards/` | Token (member) | Create card |
| GET | `/cards/{id}/` | Token | Full card detail |
| PATCH | `/cards/{id}/` | Token (member) | Update card |
| DELETE | `/cards/{id}/` | Token (member) | Delete card |
| POST | `/cards/{id}/move/` | Token (member) | Move to new position / list |
| POST | `/cards/{id}/archive/` | Token (member) | Soft-delete (archive) |
| POST | `/cards/{id}/unarchive/` | Token (member) | Restore archived card |

**Query params:** `?list=<id>` · `?board=<id>` · `?archived=true|false` · `?search=<text>`

**Move payload:**
```json
{ "position": 2, "list_id": 5 }
```

### Labels

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/labels/` | Token | Labels for accessible boards |
| POST | `/labels/` | Token (admin) | Create label |
| PATCH | `/labels/{id}/` | Token (admin) | Update label |
| DELETE | `/labels/{id}/` | Token (admin) | Delete label |

**Query params:** `?board=<id>`

### Checklists

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/checklists/` | Token | Checklists for accessible cards |
| POST | `/checklists/` | Token (member) | Add checklist to card |
| PATCH | `/checklists/{id}/` | Token (member) | Rename / reorder |
| DELETE | `/checklists/{id}/` | Token (member) | Delete checklist |

**Query params:** `?card=<id>`

Checklist response includes `items_total` and `items_checked` for progress bars.

### Checklist Items

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/checklist-items/` | Token | Items for accessible checklists |
| POST | `/checklist-items/` | Token (member) | Add item |
| PATCH | `/checklist-items/{id}/` | Token (member) | Toggle `checked`, rename |
| DELETE | `/checklist-items/{id}/` | Token (member) | Delete item |

**Query params:** `?checklist=<id>`

### Comments

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/comments/` | Token | Comments for accessible cards |
| POST | `/comments/` | Token (member) | Add comment |
| PATCH | `/comments/{id}/` | Token (author or admin) | Edit comment |
| DELETE | `/comments/{id}/` | Token (author or admin) | Delete comment |

**Query params:** `?card=<id>`

Response includes `is_edited: true|false` based on `updated_at` vs `created_at`.

### Attachments

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/attachments/` | Token | Attachments for accessible cards |
| POST | `/attachments/` | Token (member) | Register attachment metadata |
| DELETE | `/attachments/{id}/` | Token (uploader or admin) | Delete attachment record |

**Query params:** `?card=<id>`

> File storage is URL-based. Integrate with S3/Cloudinary and pass the URL + metadata.

### Board Members

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/board-members/` | Token | Members of boards you're in |
| POST | `/board-members/` | Token (admin) | Add member directly |
| PATCH | `/board-members/{id}/` | Token (admin) | Change role |
| DELETE | `/board-members/{id}/` | Token (admin) | Remove member |

### Card Members

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/card-members/` | Token | Assignments on accessible cards |
| POST | `/card-members/` | Token (member) | Assign board member to card |
| DELETE | `/card-members/{id}/` | Token (member) | Unassign |

**Query params:** `?card=<id>`

> Only existing board members can be assigned to cards.

### Invitations

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/invitations/` | Token (admin) | Pending invitations for your boards |
| DELETE | `/invitations/{id}/` | Token (admin) | Cancel invitation |
| POST | `/invitations/accept/` | Token | Accept with `{token: "<uuid>"}` |

### Activity Feed

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/activities/` | Token | Activity feed for accessible boards |
| GET | `/activities/{id}/` | Token | Single activity entry |

**Query params:** `?board=<id>` · `?card=<id>`

Activity feed is **read-only** — records are created automatically by Django signals.

---

## Authentication

The API uses **Token Authentication** (REST Framework).

### Register
```http
POST /api/register/
Content-Type: application/json

{
  "username": "alice",
  "email": "alice@example.com",
  "password": "StrongPass123!",
  "first_name": "Alice",
  "last_name": "Dupont"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Compte créé avec succès.",
  "data": {
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user": { "user_id": 1, "username": "alice", ... }
  }
}
```

### Use the token
Include the token in every subsequent request:
```http
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

---

## Role-based Permissions

| Action | Observer | Member | Admin | Creator |
|---|:---:|:---:|:---:|:---:|
| View board | ✅ | ✅ | ✅ | ✅ |
| Create list / card | ❌ | ✅ | ✅ | ✅ |
| Edit list / card | ❌ | ✅ | ✅ | ✅ |
| Delete list | ❌ | ❌ | ✅ | ✅ |
| Manage labels | ❌ | ❌ | ✅ | ✅ |
| Invite members | ❌ | ❌ | ✅ | ✅ |
| Change member role | ❌ | ❌ | ✅ | ✅ |
| Archive / close board | ❌ | ❌ | ✅ | ✅ |
| Edit own comment | ❌ | ✅ | ✅ | ✅ |
| Delete any comment | ❌ | ❌ | ✅ | ✅ |

**Public boards** are readable by any authenticated user without membership.

---

## Query Filters

All list endpoints support standard query parameters:

| Parameter | Type | Description |
|---|---|---|
| `?board=<id>` | integer | Filter by board |
| `?list=<id>` | integer | Filter by list |
| `?card=<id>` | integer | Filter by card |
| `?checklist=<id>` | integer | Filter by checklist |
| `?archived=true\|false` | boolean | Filter archived items |
| `?is_closed=true\|false` | boolean | Filter closed boards |
| `?visibility=public\|private\|workspace` | string | Filter boards by visibility |
| `?search=<text>` | string | Full-text search (cards only: title + description) |
| `?page=<n>` | integer | Page number (default page size: 20) |

---

## Activity Feed

Activities are created automatically by Django signals for:

| Action Type | Trigger |
|---|---|
| `create_board` | Board created |
| `join_board` | User joins via invitation or direct add |
| `leave_board` | User removed from board |
| `add_comment` | Comment posted on a card |
| `delete_comment` | Comment deleted |
| `check_item` / `uncheck_item` | Checklist item toggled |

Additional actions are logged directly in ViewSets for card creation, moves, and archival.

**Example response:**
```json
{
  "activity_id": 42,
  "board": 1,
  "card": 7,
  "list": null,
  "user": 3,
  "user_details": { "username": "alice", "avatar_url": "..." },
  "action_type": "add_comment",
  "content": "a commenté la carte « Fix login bug ».",
  "created_at": "2026-05-16T14:30:00Z"
}
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd API_TO_DO_APP

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Create a superuser (optional)
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`.  
Swagger UI: `http://localhost:8000/swagger/`

---

## Environment Variables

Copy `.env.example` to `.env` and set the following variables:

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | *(insecure placeholder)* | Long random secret key |
| `DJANGO_DEBUG` | `True` | Set to `False` in production |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | Comma-separated hostnames |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,...` | Comma-separated frontend origins |
| `EMAIL_HOST_USER` | *(your Gmail)* | SMTP sender address |
| `EMAIL_HOST_PASSWORD` | *(your App Password)* | Gmail App Password |
| `API_BASE_URL` | `http://localhost:8000/api/` | Used by the optional Django template frontend |

> **Production:** Replace SQLite with PostgreSQL by setting `DB_*` variables and uncommenting the PostgreSQL config block in `settings.py`.

---

## Frontend Integration Guide

### Recommended Stack
React (Next.js 14+ App Router) · TypeScript · TanStack Query · Axios

### Base Axios instance

```typescript
// lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Token ${token}`;
  return config;
});

export default api;
```

### Authentication flow

```typescript
// 1. Register
const { data } = await api.post('/register/', { username, email, password });
localStorage.setItem('token', data.data.token);

// 2. Login
const { data } = await api.post('/login/', { email, password });
localStorage.setItem('token', data.data.token);

// 3. Logout
await api.post('/logout/');
localStorage.removeItem('token');
```

### Load a board

```typescript
// GET /api/boards/1/  → board detail with lists summary + members
const { data: board } = await api.get('/boards/1/');

// GET /api/lists/?board=1  → lists with cards (paginated)
const { data } = await api.get('/lists/', { params: { board: 1 } });
const lists = data.results;  // PaginatedResponse<List>
```

### Drag-and-drop card move

```typescript
// Move card 7 to list 3 at position 1
await api.post('/cards/7/move/', { position: 1, list_id: 3 });
```

### Checklist progress bar

```typescript
// ChecklistSerializer exposes items_total and items_checked
const progress = checklist.items_total > 0
  ? Math.round((checklist.items_checked / checklist.items_total) * 100)
  : 0;
```

### Pagination pattern

```typescript
interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

const loadMore = async (url: string) => {
  const { data } = await axios.get<PaginatedResponse<Card>>(url);
  return data;
};
```

### Response envelope

All API responses follow a consistent shape:

**Success:**
```json
{ "success": true, "message": "...", "data": { ... } }
```

**Error:**
```json
{ "success": false, "message": "...", "errors": { "field": ["detail"] } }
```

---

## Roadmap

### Short-term (v1.1)
- [ ] Real-time updates via Django Channels (WebSockets)
- [ ] File upload endpoint (S3 / Cloudinary integration)
- [ ] Due date email reminders (Celery + Beat)
- [ ] @mention notifications in comments

### Medium-term (v1.2)
- [ ] Board templates (clone a board structure)
- [ ] Card cover colors + gradient backgrounds
- [ ] Advanced filtering (filter cards by label, member, due date range)
- [ ] Bulk card operations (archive, move, delete multiple)

### Long-term (v2.0)
- [ ] Webhook system (POST to external URLs on board events)
- [ ] Custom fields on cards
- [ ] Time tracking per card
- [ ] Guest access (view-only public board link without account)

---

## License

MIT — see [LICENSE](LICENSE) for details.
