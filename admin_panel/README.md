# Django Admin Panel — Blog Management API

A real Django Admin, reading and writing the **same `blog.db` SQLite file**
your FastAPI app uses — via unmanaged models, so Django never creates or
alters that schema (FastAPI/SQLAlchemy still owns it entirely). This gives
you an actual Django Admin for the screenshots your brief asks for, instead
of a FastAPI/Swagger substitute.

## Setup (run this after your FastAPI app has been started at least once,
so `blog.db` and its tables — including `subscription_plans` and
`billing_history` — already exist)

```bash
cd admin_panel
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

python manage.py migrate
```

`migrate` only creates Django's own internal tables (`auth_user`,
`django_session`, etc.) inside the same `blog.db` file — it does not touch
`users`, `posts`, `subscription_plans`, or `billing_history`.

Create your Django Admin login (separate from any FastAPI user account):

```bash
python manage.py createsuperuser
```

Then start it on a different port from FastAPI:

```bash
python manage.py runserver 8001
```

Open **http://127.0.0.1:8001/admin/** and log in with the superuser you
just created.

## What you'll see

- **Users** — every registered user, their email, and their current
  subscription plan
- **Subscription Plans** — Basic / Premium / Pro with every limit column
  and a live count of subscribers on each plan
- **Billing History** — every subscription/upgrade event, with amount,
  start/end dates, and a clickable link to that transaction's invoice PDF
  (served by the FastAPI app, so keep `uvicorn` running on port 8000 too if
  you want the invoice links to open)
- **Posts / Comments / Likes** — read-only views of the content itself

## Important: run this *alongside* FastAPI, not instead of it

This Django project only manages **data visibility** (viewing/editing rows
directly). It does **not** replace any FastAPI functionality — registration,
login, posting, limit enforcement, and invoice generation all still happen
through the FastAPI API exactly as before. Keep both servers running:

- FastAPI: `uvicorn app.main:app --reload` → port 8000
- Django Admin: `python manage.py runserver 8001` → port 8001

## A note on "validation messages for users who exceed their limits"

That specific check — blocking a 6th post/comment/like with
`"You've reached your plan limit. Kindly upgrade your plan to continue."`
— happens at the moment a user tries to *create* something, which only the
FastAPI API does (via `POST /posts`, `POST /posts/{id}/comments`, etc.).
Django Admin doesn't process those same create-requests, so that exact
validation message can only be captured from **Swagger** (`/docs`), not
from Django Admin. Django Admin shows you the *result* — e.g. a user stuck
on Basic with exactly 1 post — but the error message itself is an API-level
response, captured separately.
