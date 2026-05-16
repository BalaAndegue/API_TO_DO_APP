# Collaborative Workspace API

> A professional **Trello-like** REST API built with **Django 5** & **Django REST Framework**.  
> Boards · Lists · Cards · Checklists · Labels · Comments · Attachments · Real-time Activity Feed · Role-based Access Control

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Data Model (ER Diagram)](#data-model-er-diagram)
- [API Flow Diagrams](#api-flow-diagrams)
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
| **Activity Feed** | Auto-logged audit trail via Django signals |
| **Search** | Card full-text search on title + description |
| **Pagination** | All list endpoints paginated (20 items/page) |

---

## System Architecture

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        FE["Frontend\nReact / Next.js"]
        MOBILE["Mobile App\niOS / Android"]
    end

    subgraph API["Django REST Framework API"]
        direction TB
        AUTH["Auth Layer\nToken Authentication"]
        ROUTER["URL Router\n/api/*"]
        VS["ViewSets\n14 resources"]
        PERM["Permission Layer\nIsBoardMember · IsBoardAdmin · IsOwner"]
        SER["Serializers\nLight + Detail layers"]
        SIGNALS["Django Signals\nActivity auto-logging"]
    end

    subgraph Data["Data Layer"]
        ORM["Django ORM\nselect_related · prefetch_related"]
        DB[("SQLite (dev)\nPostgreSQL (prod)")]
    end

    subgraph Infra["External Services"]
        SMTP["SMTP\nGmail / SendGrid"]
        STORE["File Storage\nS3 / Cloudinary"]
    end

    Client -->|"Authorization: Token ..."| AUTH
    AUTH --> ROUTER
    ROUTER --> VS
    VS --> PERM
    PERM --> SER
    SER --> ORM
    ORM --> DB
    VS --> SIGNALS
    SIGNALS --> DB
    VS -->|"send_mail()"| SMTP
    VS -->|"URL metadata"| STORE
```

---

## Data Model (ER Diagram)

```mermaid
erDiagram
    USER {
        int user_id PK
        string username
        string email
        string first_name
        string last_name
        string bio
        string avatar_url
        datetime created_at
        bool is_active
    }

    BOARD {
        int board_id PK
        string name
        string description
        string visibility
        string background_type
        string background_value
        int position
        bool is_closed
        datetime created_at
    }

    BOARD_MEMBER {
        int id PK
        string role
        datetime joined_at
    }

    BOARD_INVITATION {
        int id PK
        string email
        uuid token
        bool accepted
        datetime created_at
    }

    LIST {
        int list_id PK
        string name
        int position
        bool archived
        datetime created_at
    }

    CARD {
        int card_id PK
        string title
        string description
        datetime start_date
        datetime due_date
        bool due_date_complete
        string cover_image_url
        int position
        bool archived
        datetime created_at
    }

    LABEL {
        int label_id PK
        string name
        string color
        bool archived
    }

    CARD_LABEL {
        int id PK
    }

    CARD_MEMBER {
        int id PK
        datetime added_at
    }

    CHECKLIST {
        int checklist_id PK
        string name
        int position
        datetime created_at
    }

    CHECKLIST_ITEM {
        int item_id PK
        string name
        bool checked
        int position
        datetime created_at
    }

    COMMENT {
        int comment_id PK
        string content
        datetime created_at
        datetime updated_at
    }

    ATTACHMENT {
        int attach_id PK
        string filename
        string url
        string mime_type
        int size
        datetime uploaded_at
    }

    ACTIVITY {
        int activity_id PK
        string action_type
        string content
        datetime created_at
    }

    PASSWORD_RESET {
        int id PK
        uuid reset_id
        datetime created_when
    }

    USER ||--o{ BOARD : "creates"
    USER ||--o{ BOARD_MEMBER : "has role in"
    USER ||--o{ BOARD_INVITATION : "sends"
    USER ||--o{ COMMENT : "writes"
    USER ||--o{ ATTACHMENT : "uploads"
    USER ||--o{ ACTIVITY : "triggers"
    USER ||--o{ CARD_MEMBER : "assigned to"
    USER ||--o{ PASSWORD_RESET : "requests"

    BOARD ||--o{ BOARD_MEMBER : "has"
    BOARD ||--o{ BOARD_INVITATION : "receives"
    BOARD ||--o{ LIST : "contains"
    BOARD ||--o{ LABEL : "owns"
    BOARD ||--o{ ACTIVITY : "logs"

    LIST ||--o{ CARD : "contains"

    CARD ||--o{ CARD_LABEL : "tagged with"
    CARD ||--o{ CARD_MEMBER : "assigned to"
    CARD ||--o{ CHECKLIST : "has"
    CARD ||--o{ COMMENT : "receives"
    CARD ||--o{ ATTACHMENT : "has"
    CARD ||--o{ ACTIVITY : "generates"

    LABEL ||--o{ CARD_LABEL : "applied via"
    CHECKLIST ||--o{ CHECKLIST_ITEM : "contains"
```

---

## API Flow Diagrams

### Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as Django API
    participant DB as Database
    participant SMTP as Email Server

    C->>API: POST /api/register/ {username, email, password}
    API->>DB: Create User (set_password)
    API->>DB: Create Token
    API-->>C: 201 {token, user}

    C->>API: POST /api/login/ {email, password}
    API->>DB: Lookup User by email
    API->>API: check_password()
    API->>DB: Get or create Token
    API-->>C: 200 {token, user}

    C->>API: POST /api/logout/ [Authorization: Token ...]
    API->>DB: Delete Token
    API-->>C: 200 {success: true}

    C->>API: POST /api/users/change_password/ {new_password}
    API->>API: validate_password()
    API->>DB: set_password + rotate Token
    API-->>C: 200 {new_token}

    C->>API: POST /api/ (forgot password - template frontend)
    API->>DB: Create PasswordReset (UUID token)
    API->>SMTP: Send reset link by email
    API-->>C: Redirect to confirmation page
```

### Board Invitation Flow

```mermaid
sequenceDiagram
    participant ADMIN as Board Admin
    participant API as Django API
    participant DB as Database
    participant SMTP as Email Server
    participant GUEST as Invited User

    ADMIN->>API: POST /api/boards/{id}/invite/ {email}
    API->>DB: Check: already member?
    API->>DB: Check: invitation pending?
    API->>DB: Create BoardInvitation (UUID token)
    API->>SMTP: Send invitation email with token
    API-->>ADMIN: 201 {invitation details}

    GUEST->>API: POST /api/invitations/accept/ {token}
    API->>DB: Get invitation WHERE token=? AND accepted=False
    Note over API,DB: Atomic transaction begins
    API->>DB: invitation.accepted = True
    API->>DB: Create BoardMember (role: member)
    Note over API,DB: Atomic transaction ends
    API-->>GUEST: 200 {board_id, board_name}
```

### Card Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Active : POST /cards/

    Active --> Active : PATCH /cards/{id}/\n(edit title, description, dates)
    Active --> Active : POST /cards/{id}/move/\n(change list or position)
    Active --> Archived : POST /cards/{id}/archive/

    Archived --> Active : POST /cards/{id}/unarchive/
    Archived --> [*] : DELETE /cards/{id}/

    Active --> [*] : DELETE /cards/{id}/

    state Active {
        [*] --> NoLabel
        NoLabel --> Labelled : POST /card-labels/
        Labelled --> NoLabel : DELETE /card-labels/{id}/
    }
```

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
| GET | `/boards/{id}/` | Token | Board detail with lists + members |
| PATCH | `/boards/{id}/` | Token (member) | Update board metadata |
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

Response includes `items_total` and `items_checked` for progress bar rendering.

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
| DELETE | `/attachments/{id}/` | Token (uploader or admin) | Delete attachment |

**Query params:** `?card=<id>`

> File storage is URL-based. Integrate with S3/Cloudinary and pass the `url` + metadata.

### Board Members

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/board-members/` | Token | Members of your boards |
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

### Invitations

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/invitations/` | Token (admin) | Pending invitations for your boards |
| DELETE | `/invitations/{id}/` | Token (admin) | Cancel invitation |
| POST | `/invitations/accept/` | Token | Accept with `{"token": "<uuid>"}` |

### Activity Feed

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/activities/` | Token | Activity feed for accessible boards |
| GET | `/activities/{id}/` | Token | Single activity entry |

**Query params:** `?board=<id>` · `?card=<id>`

Activity feed is **read-only** — records are created automatically by Django signals.

---

## Authentication

The API uses **Token Authentication** (REST Framework `authtoken`).

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

**Response `201`:**
```json
{
  "success": true,
  "message": "Compte créé avec succès.",
  "data": {
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user": { "user_id": 1, "username": "alice", "email": "alice@example.com" }
  }
}
```

### Include the token in every request
```http
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

---

## Role-based Permissions

```mermaid
flowchart LR
    subgraph Roles
        OB["Observer"]
        ME["Member"]
        AD["Admin"]
        CR["Creator"]
    end

    OB -->|"inherits"| ME
    ME -->|"inherits"| AD
    AD -->|"inherits"| CR

    subgraph Actions
        READ["View board & cards"]
        WRITE["Create & edit lists/cards"]
        MANAGE["Delete lists · Manage labels"]
        ADMIN_ACTIONS["Invite · Change roles · Close board"]
    end

    OB --> READ
    ME --> WRITE
    AD --> MANAGE
    CR --> ADMIN_ACTIONS
```

| Action | Observer | Member | Admin | Creator |
|---|:---:|:---:|:---:|:---:|
| View board & public cards | ✅ | ✅ | ✅ | ✅ |
| Create list / card / comment | ❌ | ✅ | ✅ | ✅ |
| Edit list / card | ❌ | ✅ | ✅ | ✅ |
| Delete list | ❌ | ❌ | ✅ | ✅ |
| Manage labels | ❌ | ❌ | ✅ | ✅ |
| Invite members | ❌ | ❌ | ✅ | ✅ |
| Change member role | ❌ | ❌ | ✅ | ✅ |
| Archive / close board | ❌ | ❌ | ✅ | ✅ |
| Edit own comment | ❌ | ✅ | ✅ | ✅ |
| Delete any comment | ❌ | ❌ | ✅ | ✅ |
| Delete attachment (own) | ❌ | ✅ | ✅ | ✅ |

---

## Query Filters

All list endpoints support these query parameters:

| Parameter | Type | Supported on |
|---|---|---|
| `?board=<id>` | integer | lists, cards, labels, activities |
| `?list=<id>` | integer | cards |
| `?card=<id>` | integer | checklists, checklist-items, comments, attachments, card-members, card-labels |
| `?checklist=<id>` | integer | checklist-items |
| `?archived=true\|false` | boolean | lists, cards |
| `?is_closed=true\|false` | boolean | boards |
| `?visibility=...` | string | boards |
| `?search=<text>` | string | cards (title + description) |
| `?page=<n>` | integer | all list endpoints |

---

## Activity Feed

Activities are created automatically by Django signals for:

| `action_type` | Trigger |
|---|---|
| `create_board` | Board created |
| `join_board` | User joins via invitation or direct add |
| `leave_board` | User removed from board |
| `add_comment` | Comment posted on a card |
| `delete_comment` | Comment deleted |
| `check_item` | Checklist item checked |
| `uncheck_item` | Checklist item unchecked |

**Example response:**
```json
{
  "activity_id": 42,
  "board": 1,
  "card": 7,
  "user_details": { "username": "alice", "avatar_url": "https://..." },
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
# 1. Clone the repository
git clone https://github.com/your-username/API_TO_DO_APP.git
cd API_TO_DO_APP

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env.local
# Edit .env.local with your actual values

# 5. Apply database migrations
python manage.py migrate

# 6. (Optional) Create an admin account
python manage.py createsuperuser

# 7. Start the development server
python manage.py runserver
```

| URL | Description |
|---|---|
| `http://localhost:8000/api/` | REST API |
| `http://localhost:8000/swagger/` | Interactive Swagger UI |
| `http://localhost:8000/redoc/` | ReDoc documentation |
| `http://localhost:8000/admin/` | Django admin |

---

## Environment Variables

```bash
# Copy the template and fill in real values
cp .env.example .env.local
```

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | *(insecure placeholder)* | Long random secret key |
| `DJANGO_DEBUG` | `True` | Set to `False` in production |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | Comma-separated hostnames |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,...` | Comma-separated frontend origins |
| `EMAIL_HOST_USER` | — | Gmail sender address |
| `EMAIL_HOST_PASSWORD` | — | Gmail App Password |
| `API_BASE_URL` | `http://localhost:8000/api/` | Used by Django template frontend |

> **Generate a secure secret key:**
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

> **Production:** Uncomment the PostgreSQL block in `settings.py` and set `DB_*` variables.

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

### Authentication

```typescript
// Register
const { data } = await api.post('/register/', { username, email, password });
localStorage.setItem('token', data.data.token);

// Login
const { data } = await api.post('/login/', { email, password });
localStorage.setItem('token', data.data.token);

// Logout
await api.post('/logout/');
localStorage.removeItem('token');

// Get own profile
const { data } = await api.get('/users/me/');
```

### Load a board with its lists and cards

```typescript
// Board summary (fast — no nested cards)
const { data: board } = await api.get('/boards/1/');

// Lists with lightweight cards
const { data } = await api.get('/lists/', { params: { board: 1 } });
const lists: List[] = data.results;

// Full card detail
const { data: card } = await api.get('/cards/7/');
```

### Drag-and-drop card move

```typescript
// Move card 7 to list 3 at position index 1
await api.post('/cards/7/move/', { position: 1, list_id: 3 });
```

### Checklist progress bar

```typescript
// ChecklistSerializer exposes items_total and items_checked
const percent = checklist.items_total > 0
  ? Math.round((checklist.items_checked / checklist.items_total) * 100)
  : 0;
// <progress value={percent} max={100} />
```

### Pagination pattern

```typescript
interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

const { data } = await api.get<PaginatedResponse<Card>>('/cards/', {
  params: { board: 1, page: 2 },
});
```

### Consistent response envelope

All API responses follow:

```typescript
// Success
{ success: true, message: string, data: T }

// Error
{ success: false, message: string, errors?: Record<string, string[]> }
```

---

## Project Structure

```
API_TO_DO_APP/
├── .env.example                 ← Template des variables d'environnement (versionné)
├── .env.local                   ← Variables locales (ignoré par git)
├── .gitignore
├── requirements.txt
├── manage.py
│
├── AuthenticationProject/       ← Projet Django (configuration)
│   ├── settings.py              ← Config env-aware avec python-dotenv
│   ├── urls.py                  ← Swagger + routing principal
│   └── wsgi.py
│
└── Core/                        ← Application principale
    ├── models.py                ← 14 modèles
    ├── serializers.py           ← Couches light/detail
    ├── permissions.py           ← IsBoardMember · IsBoardAdmin · IsOwner
    ├── signals.py               ← Activity auto-logging
    ├── utils.py                 ← Exception handler
    ├── apps.py                  ← Enregistrement des signaux
    ├── views.py                 ← Frontend Django templates
    │
    └── ViewSet/                 ← Un ViewSet par ressource
        ├── UserViewSet.py       ← Auth + profil
        ├── BoardViewSet.py      ← Boards + invite/close/reopen
        ├── ListViewSet.py
        ├── CardViewSet.py       ← CRUD + move/archive
        ├── LabelViewSet.py
        ├── ChecklistViewSet.py
        ├── ChecklistItemViewSet.py
        ├── CommentViewSet.py
        ├── AttachmentViewSet.py
        ├── CardMemberViewSet.py
        ├── CardLabelViewSet.py
        ├── BoardMemberViewSet.py
        ├── ActivityViewSet.py   ← Read-only feed
        └── BoardInvitationViewSet.py
```

---

## Roadmap

### v1.1 — Short-term
- [ ] Real-time updates via Django Channels (WebSockets)
- [ ] File upload endpoint (S3 / Cloudinary integration)
- [ ] Due date email reminders (Celery + Beat)
- [ ] @mention notifications in comments

### v1.2 — Medium-term
- [ ] Board templates (clone a board structure)
- [ ] Advanced card filtering (by label, member, due date range)
- [ ] Bulk card operations (archive, move multiple)
- [ ] Card cover colors + gradient backgrounds

### v2.0 — Long-term
- [ ] Webhook system (POST to external URLs on board events)
- [ ] Custom fields on cards
- [ ] Time tracking per card
- [ ] Guest access (view-only public board link without account)

---

## License

MIT — see [LICENSE](LICENSE) for details.
