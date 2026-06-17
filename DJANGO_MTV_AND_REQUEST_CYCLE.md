# Django MTV Architecture & Request Cycle — UEMS Project

---

## 1. What is MTV?

Django follows the **MTV** pattern — **Model, Template, View**. It is Django's equivalent of the classic MVC pattern, with a different name for the "Controller" layer.

| Layer | Django Name | Responsibility |
|-------|------------|----------------|
| Data / DB logic | **Model** | Defines database tables, relationships, and business data rules |
| Presentation | **Template** | HTML files that render data to the browser |
| Request handler | **View** | Receives HTTP requests, queries Models, picks a Template, returns a response |

Django's URL dispatcher (URLconf) is the part that routes incoming URLs to the right View — it plays the role of the "Controller" in MVC.

---

## 2. Project Folder Map & MTV Roles

```
uems/                          ← Django project root (manage.py lives here)
│
├── manage.py                  ← CLI entry point (runserver, migrate, etc.)
│
├── uems/                      ← Project package (settings, root URL config, WSGI/ASGI)
│   ├── settings.py            ← Configuration (INSTALLED_APPS, DATABASES, TEMPLATES, MIDDLEWARE...)
│   ├── urls.py                ← ROOT URLconf — first URL dispatcher Django reads
│   ├── wsgi.py                ← WSGI entry point for production servers (e.g., gunicorn)
│   └── asgi.py                ← ASGI entry point (async capable deployments)
│
├── accounts/                  ← "accounts" Django app
│   ├── models.py              ← [MODEL] Profile model (extends Django's built-in User)
│   ├── views.py               ← [VIEW]  home, register, login_view, verify_email, logout_view
│   ├── urls.py                ← [URL]   URL patterns for /accounts/ routes
│   ├── forms.py               ← [FORM]  RegisterForm (ModelForm wrapping User)
│   ├── admin.py               ← Registers Profile in Django Admin
│   ├── apps.py                ← App config (AccountsConfig)
│   └── migrations/            ← Auto-generated DB migration files
│       ├── 0001_initial.py
│       └── 0002_...py
│
├── events/                    ← "events" Django app
│   ├── models.py              ← [MODEL] Event, Category, EventRegistration, EventProposal,
│   │                                    Announcement, Feedback, Notification models
│   ├── views.py               ← [VIEW]  dashboard, available_events, view_event,
│   │                                    register_event, generate_qr, submit_proposal, etc.
│   ├── urls.py                ← [URL]   URL patterns for all event-related routes
│   ├── forms.py               ← [FORM]  Event and proposal-related forms
│   ├── context_processors.py  ← Injects notifications into every template's context
│   ├── notification_router.py ← Custom logic for creating/routing notifications
│   ├── admin.py               ← Registers event models in Django Admin
│   ├── apps.py                ← App config (EventsConfig)
│   ├── management/            ← Custom management commands (e.g., mark_absent)
│   │   └── commands/
│   └── migrations/            ← DB migration history (0001 → 0025+)
│
├── core/                      ← "core" app (shared / utility layer)
│   ├── models.py
│   └── views.py
│
├── templates/                 ← Project-level templates directory
│   ├── base.html              ← Master base template (all pages extend this)
│   ├── home.html
│   └── accounts/             ← App-scoped template subfolder
│
└── events/
    └── templates/
        └── events/            ← App-level templates for events app
            ├── dashboard.html
            ├── available_events.html
            ├── view_event.html
            ├── register_event.html
            ├── generate_qr.html
            └── ... (18 templates total)
```

---

## 3. Each File's Role in MTV

### Models (`models.py`)
The **M** in MTV. Each class = one database table.

| File | Models Defined |
|------|---------------|
| `accounts/models.py` | `Profile` — extends Django's `User` with `role`, `email_verified`, `verification_token`, `is_organizer` |
| `events/models.py` | `Event`, `Category`, `EventRegistration`, `EventProposal`, `Announcement`, `Feedback`, `Notification` |

Django's built-in `User` model (from `django.contrib.auth`) is also used — `Profile` is linked to it via `OneToOneField`.

---

### Views (`views.py`)
The **V** in MTV (what MVC calls "Controller"). Views are Python functions (function-based views in this project) that:
1. Receive an `HttpRequest` object
2. Query models / run business logic
3. Pass a context dictionary to a template
4. Return an `HttpResponse` (usually via `render()`)

| File | Key Views |
|------|-----------|
| `accounts/views.py` | `home`, `register`, `login_view`, `verify_email`, `logout_view` |
| `events/views.py` | `dashboard`, `available_events`, `view_event`, `register_event`, `generate_qr`, `submit_proposal`, `view_proposals`, `send_announcement`, `feedback`, `notifications`, etc. |

---

### Templates (`templates/`)
The **T** in MTV. Pure HTML + Django Template Language (DTL).

**Two template locations are configured in `settings.py`:**

```python
# settings.py
TEMPLATES = [{
    'DIRS': [BASE_DIR / "templates"],   # ← project-level templates/
    'APP_DIRS': True,                   # ← also searches each app's templates/ subfolder
}]
```

| Location | Used for |
|----------|----------|
| `uems/templates/base.html` | Master layout — navbar, footer, CSS/JS includes |
| `uems/templates/accounts/` | Account-related pages (login, register) |
| `uems/events/templates/events/` | All event pages (dashboard, proposals, QR, etc.) |

Templates inherit from `base.html` using `{% extends "base.html" %}`.

---

### Forms (`forms.py`)
Not strictly part of MTV, but essential. Forms handle input validation and HTML form rendering.

| File | Forms |
|------|-------|
| `accounts/forms.py` | `RegisterForm` — a `ModelForm` wrapping Django's `User` model |
| `events/forms.py` | Event and proposal forms |

---

### URL Configuration (`urls.py`)
The **URL dispatcher** is the glue between the browser's request and the View.

```
uems/urls.py          ← ROOT_URLCONF (set in settings.py)
  ├── admin/          → Django Admin
  ├── ''              → accounts_views.home
  ├── accounts/       → include('accounts.urls')
  └── ''              → include('events.urls')   ← events at root level (no prefix)
```

---

## 4. The Full HTTP Request Cycle

Here is a step-by-step walkthrough of what happens when a user navigates to `http://127.0.0.1:8000/event/5/` in this project:

```
Browser
  │
  │  GET /event/5/
  ▼
┌─────────────────────────────────────────────────┐
│  WSGI Server  (manage.py runserver / gunicorn)  │
│  Entry point: uems/wsgi.py                      │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  MIDDLEWARE STACK  (settings.py → MIDDLEWARE)   │
│                                                 │
│  1. SecurityMiddleware                          │
│  2. SessionMiddleware    ← loads session/cookie │
│  3. CommonMiddleware                            │
│  4. CsrfViewMiddleware   ← validates CSRF token │
│  5. AuthenticationMiddleware ← attaches         │
│       request.user from session                 │
│  6. MessageMiddleware                           │
│  7. XFrameOptionsMiddleware                     │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  ROOT URLconf:  uems/urls.py                    │
│                                                 │
│  urlpatterns = [                                │
│    path('', include('events.urls')),            │
│  ]                                              │
│                                                 │
│  Delegates to events/urls.py                   │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  App URLconf:  events/urls.py                   │
│                                                 │
│  path('event/<int:event_id>/',                  │
│       views.view_event,                         │
│       name='view_event')                        │
│                                                 │
│  Matched! event_id = 5                          │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  VIEW:  events/views.py → view_event(request,   │
│                                    event_id=5)  │
│                                                 │
│  1. Queries Model:                              │
│     event = Event.objects.get(pk=5)             │
│                                                 │
│  2. Builds context dict:                        │
│     context = {'event': event, ...}             │
│                                                 │
│  3. Calls render():                             │
│     return render(request,                      │
│       'events/view_event.html', context)        │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  CONTEXT PROCESSOR  (events/context_processors) │
│                                                 │
│  notifications_context(request) is called       │
│  automatically and merges into context:         │
│  { 'notifications': [...], 'unread_count': N }  │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  TEMPLATE ENGINE                                │
│                                                 │
│  Locates: events/templates/events/view_event    │
│                                          .html  │
│  Extends:  base.html  (project-level)           │
│  Renders:  DTL tags {{ event.name }},           │
│            {% if %}, {% for %}, {% url %}, etc. │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  MIDDLEWARE STACK  (response phase, reversed)   │
│  (e.g., adds session cookie, security headers)  │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
                  Browser
              Receives HTML page
```

---

## 5. Another Example — POST Request (User Registration)

`POST /accounts/register/`

1. **Root URLconf** (`uems/urls.py`) — matches `accounts/` prefix → delegates to `accounts/urls.py`
2. **accounts/urls.py** — matches `register/` → calls `views.register`
3. **`CsrfViewMiddleware`** — validates the `{% csrf_token %}` in the form
4. **`accounts/views.py` → `register()`**:
   - Instantiates `RegisterForm(request.POST)`
   - Calls `form.is_valid()` — runs field-level validation
   - Creates `User` and `Profile` (Model layer)
   - Calls `send_mail()` for email verification
   - Redirects with `redirect('login')`
5. **Response** — `302 Redirect` back to the browser

---

## 6. Does This Project Follow Standard Django Practices?

| Practice | Standard? | Notes |
|----------|-----------|-------|
| One `models.py` per app | ✅ Yes | `accounts/models.py`, `events/models.py` |
| One `views.py` per app | ✅ Yes | FBVs (function-based views) — valid approach |
| App-level `urls.py` included from root | ✅ Yes | `include('accounts.urls')`, `include('events.urls')` |
| App-level `templates/<app_name>/` folder | ✅ Yes | `events/templates/events/` follows Django namespacing convention |
| Project-level `templates/` for shared templates | ✅ Yes | `base.html` lives in project-level `templates/` |
| `migrations/` folder per app | ✅ Yes | All apps have full migration history |
| `admin.py` per app | ✅ Yes | Models registered with custom `ModelAdmin` classes |
| `forms.py` per app | ✅ Yes | `ModelForm` used — correct Django pattern |
| Custom context processor registered in `settings.py` | ✅ Yes | `events.context_processors.notifications_context` |
| `apps.py` per app | ✅ Yes | App config classes present |
| Management commands in `management/commands/` | ✅ Yes | `events/management/commands/` (e.g., `mark_absent`) |
| `ROOT_URLCONF` set in settings | ✅ Yes | `ROOT_URLCONF = 'uems.urls'` |
| `APP_DIRS: True` for template discovery | ✅ Yes | Allows per-app template lookup |
| `SECRET_KEY` is insecure placeholder | ⚠️ Warning | `django-insecure-...` key is fine for dev but must be replaced before production |
| `DEBUG = True` | ⚠️ Warning | Must be `False` in production |

**Verdict: The project follows standard Django practices correctly.** The app separation, template namespacing, URL include hierarchy, migrations, and context processors all match Django's recommended conventions.

---

## 7. Quick Reference Cheat Sheet

```
Request URL
    ↓
uems/wsgi.py  (server entry)
    ↓
Middleware (session, auth, CSRF...)
    ↓
uems/urls.py  (ROOT_URLCONF)
    ↓
accounts/urls.py  OR  events/urls.py  (app URLconfs)
    ↓
views.py  (business logic + model queries)
    ↓
models.py  (DB access via Django ORM)
    ↓
templates/*.html  (rendered with context)
    ↓
Middleware (response phase)
    ↓
HTTP Response → Browser
```
