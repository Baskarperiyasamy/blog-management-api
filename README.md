# Blog Management API (FastAPI)

A mini blogging system built with **FastAPI + SQLAlchemy + SQLite**.
Authenticated users (JWT) can create/update/delete their own posts (with an
optional cover image), comment on posts, like/unlike posts, browse a
paginated/searchable feed, and email notifications are triggered on new
comments and likes.

---

## 🆕 v4.0 — Email Notification System (likes & comments)

| Requirement | Implementation |
|---|---|
| Email on comment / like | `routers/comments.py` and `routers/likes.py` call `notify_post_author()` right after the row is saved |
| Email content | Post title · user name · activity (Like/Comment) · timestamp — built in `services/notification_service.py` |
| SMTP sending | `services/email_service.py` (Python `smtplib`, STARTTLS on 587/2525, SSL on 465) |
| Async / non-blocking | FastAPI `BackgroundTasks` — the email is sent *after* the response is returned |
| Config | `.env` → `app/config.py` (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_FROM` …) |
| Graceful errors | `send_email()` never raises; failures are logged (`❌ ...`) and the API request still succeeds |
| Modular | `email_service` (how to send) ↔ `notification_service` (what/when to send) ↔ routers (trigger) |

Email format:
```
Post: "FastAPI Best Practices"
User: John Doe
Activity: Commented on your post
Time: 2026-03-04 11:20 AM
```

> **Rule:** the author is not emailed about their *own* likes/comments. To get an email you need **two users**:
> user A creates a post → user B likes/comments on it → A receives the email.

---

## ▶️ How to run (step by step)

**1. Open a terminal in the project folder** (the folder that contains `app/` and `requirements.txt`).

**2. Create & activate a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate        # Mac / Linux
```

**3. Install packages**
```bash
pip install -r requirements.txt
```

**4. Create the `.env` file** (THIS is the step most people miss — without `.env` no email is sent)
```bash
copy .env.example .env          # Windows
cp .env.example .env            # Mac / Linux
```
Open `.env` and fill in your Mailtrap **or** Gmail details (see below).

**5. Test your SMTP settings before starting the API**
```bash
python test_smtp.py
```
You must see `✅ SUCCESS`. If you see `❌ FAILED`, the message tells you what is wrong.

**6. Start the server**
```bash
uvicorn app.main:app --reload
```
On startup you should see `SMTP ready -> sandbox.smtp.mailtrap.io:2525`.
If you see `SMTP NOT configured`, your `.env` is missing or incomplete.

**7. Open Swagger:** http://127.0.0.1:8000/docs

---

## 📬 Option A — Mailtrap (for demo / screenshots)

1. Sign up free at https://mailtrap.io
2. Left menu → **Email Testing → Inboxes** → open **My Inbox**
3. Open the **SMTP Settings** tab → **Show credentials**
4. Copy **Username** and **Password** into `.env`:
   ```
   SMTP_HOST=sandbox.smtp.mailtrap.io
   SMTP_PORT=2525
   SMTP_USERNAME=<username from Mailtrap>
   SMTP_PASSWORD=<password from Mailtrap>
   EMAIL_FROM=notifications@blogapi.example.com
   ```
5. Run `python test_smtp.py` → refresh the Mailtrap inbox → the test email appears.
6. Every notification the app sends now lands in that Mailtrap inbox (whatever address the author registered with) — **take your screenshots there**.

## 📧 Option B — Gmail with an App Password (real inbox)

1. Go to https://myaccount.google.com/security → turn on **2-Step Verification**
2. Go to https://myaccount.google.com/apppasswords → name it `blog-api` → **Create**
3. Google shows a 16-character password like `abcd efgh ijkl mnop` — copy it (spaces are fine, the app removes them)
4. Put this in `.env`:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=yourname@gmail.com
   SMTP_PASSWORD=abcdefghijklmnop
   EMAIL_FROM=yourname@gmail.com
   ```
5. Run `python test_smtp.py` → check your Gmail inbox (and Spam).
6. **Register the post author with a real email address you can open**, because the email goes to the author's registered email.

---

## 🧪 Demo flow in Swagger (`/docs`)

1. `POST /auth/register` → user **alice** (`alice@example.com` — use a real address if using Gmail)
2. `POST /auth/register` → user **John Doe** (`john@example.com`)
3. Click **Authorize** → log in as **alice** → `POST /posts` (title `FastAPI Best Practices`) → note the post `id`
4. Click **Authorize** → **Logout**, log in as **John Doe**
5. `POST /posts/{id}/like` → alice gets a **Like** email
6. `POST /posts/{id}/comments` with `{"text": "Great post!"}` → alice gets a **Comment** email
7. Check your Mailtrap inbox / Gmail inbox → screenshot for the submission

Handy helpers: `GET /notifications/status` (shows loaded SMTP settings) and
`POST /notifications/test-email` (sends a test mail to the logged-in user and returns the exact SMTP error if it fails).

## 🛠️ Troubleshooting "I'm not getting mail"

| Symptom | Cause / Fix |
|---|---|
| Console shows `SMTP NOT configured` | `.env` file missing/misnamed. It must be named exactly `.env` (not `.env.example`, not `.env.txt`) and be next to `requirements.txt`. |
| No error, no email | You liked/commented on **your own** post — self-notifications are skipped. Use a second user. |
| `❌ SMTP login failed` | Wrong username/password. Gmail needs an **App Password**, not your normal password. |
| `TimeoutError` / `timed out` | Wrong host/port or network/firewall blocks it. Try Mailtrap port `2525` (or `587`), Gmail `587`. |
| Gmail: mail not in inbox | Check Spam; make sure `EMAIL_FROM` equals `SMTP_USERNAME`. |
| Changed `.env` but nothing changed | Restart uvicorn — settings are read at startup. |

---

### A real Django Admin now exists too (`admin_panel/`)

An earlier version of this README said there was no Django Admin, since
this whole project is FastAPI. That's still true for the API itself — but
a small **separate Django project** now exists in `admin_panel/`, reading
the exact same `blog.db` via unmanaged models, purely to give you a real
Django Admin UI for viewing Users / Subscription Plans / Billing History /
Posts / Comments / Likes. See `admin_panel/README.md` for setup. It doesn't
replace anything here — the FastAPI app still does all the actual work
(auth, limits, notifications, invoices); Django Admin is read/edit access
to the same data, nothing more.

---

## 🆕 v3.0 additions (subscription plans, access control & billing)

| Feature | Where |
|---|---|
| `SubscriptionPlan` model | `app/models.py` — one row per plan (basic/premium/pro), seeded automatically at startup |
| `BillingHistory` model | `app/models.py` — one row per subscription/renewal, links to its invoice PDF |
| Every user has an active plan | `User.plan_id`; auto-assigned to **Basic** at registration (`app/routers/auth.py`) |
| Plan-based access control | `app/plan_limits.py` — centralized checks called from `posts.py`, `likes.py`, `comments.py` |
| Friendly limit-exceeded message | Exact text from the task: *"You've reached your plan limit. Kindly upgrade your plan to continue."* (HTTP 403) |
| Invoice PDF generation (ReportLab) | `app/invoice_utils.py`, saved under `media/invoices/`, path stored in `BillingHistory.invoice_path` |
| `GET /subscriptions/plans` | Public — lists the 3 fixed plans and their limits |
| `POST /subscriptions/subscribe` | Subscribe/switch/renew a plan — body: `{"plan_name": "premium"}` — generates a BillingHistory row + invoice PDF |
| `GET /subscriptions/mine` | Current user's active plan plus live usage vs. limits |
| `GET /subscriptions/billing-history` | Current user's past subscriptions, each with an `invoice_url` |

### The three plans (as specified)

| Plan | Price | Posts | Images | Likes | Comments |
|---|---|---|---|---|---|
| Basic | $0.00 | 1 | 1 | 5 | 5 |
| Premium | $9.99 | 2 | 2 | 20 | 20 |
| Pro | $29.99 | Unlimited | Unlimited | Unlimited | Unlimited |

Prices and the like/comment limits weren't specified exactly in the task
(it only said "limited" for Basic and "moderate" for Premium), so I picked
reasonable concrete numbers — change them in `seed_subscription_plans()`
in `app/main.py` if you need different values.

### An important, honest scope note on "images per post"

The `Post` model (from the earlier image-upload milestone) supports **one
cover image per post** — there's no multi-image gallery per post. Adding
that would require a third new model (e.g. `PostImage`), but this task
explicitly says *"Create two models — SubscriptionPlan and BillingHistory."*
So `max_images_per_post` is enforced here as **total images uploaded across
all of a user's posts**, which is the closest honest equivalent without
adding an extra model. This is called out again inline as a comment in
`app/plan_limits.py`.

### How to test the limits quickly

1. Register a user → they're automatically on **Basic**.
2. `POST /posts` once → succeeds. Try it a 2nd time → `403` with the
   friendly message (Basic allows 1 post).
3. `POST /subscriptions/subscribe` with `{"plan_name": "premium"}` → now
   you can create a 2nd post, and an invoice PDF is generated.
4. `GET /subscriptions/mine` any time to see your current plan and how much
   of each limit you've used.
5. Open the returned `invoice_url` (e.g.
   `http://127.0.0.1:8000/media/invoices/<file>.pdf`) in your browser to
   view the generated invoice.

---

## 🆕 v2.0 additions (image upload + pagination/search)

| Feature | Endpoint(s) |
|---|---|
| Upload a cover image when creating a post | `POST /posts` (multipart/form-data) — alias: `POST /posts/create` |
| Replace/attach an image when updating a post | `PUT /posts/{post_id}` (multipart/form-data) — alias: `PUT /posts/{post_id}/update` |
| Paginated post feed | `GET /posts?page=1&limit=10` |
| Search posts by title/content | `GET /posts?search=keyword` |
| Both together | `GET /posts?page=1&limit=10&search=keyword` |
| View an uploaded image | `GET /media/posts/<filename>` |

**Why two routes for create/update?** The assignment specifies
`/posts/create` and `/posts/{id}/update`, while the original REST design
used `POST /posts` and `PUT /posts/{id}`. Both are wired to the exact same
function, so either path works identically — use whichever your grader
expects.

**Important — `POST /posts` and `PUT /posts/{id}` now take
`multipart/form-data`, not JSON.** This is required so an image file can be
sent in the same request. In Swagger UI this just means you'll see separate
text boxes for `title` / `content` and a file picker for `image`, instead of
one big JSON textarea — Swagger handles the encoding automatically, you
don't need to do anything special.

**`GET /posts` response shape changed.** It now returns an object instead
of a bare array, so pagination metadata can be included:
```json
{
  "total": 5,
  "page": 1,
  "limit": 10,
  "total_pages": 1,
  "results": [ ...posts... ]
}
```

**Image validation:** only `jpeg`, `png`, `webp`, `gif` are accepted, max
5MB. Uploaded files are saved under `media/posts/` with a random filename
and served back at `/media/posts/<filename>`. Updating a post's image
deletes the old file; deleting a post deletes its image too.

---

## ✅ Requirement checklist (where each thing lives)

| Requirement | Where it is |
|---|---|
| User (id, username, email, hashed password) | `app/models.py` → `User` |
| Post (id, title, content, author_id, created_at) | `app/models.py` → `Post` |
| Comment (id, post_id, user_id, text, created_at) | `app/models.py` → `Comment` |
| Like (id, post_id, user_id) | `app/models.py` → `Like` |
| SQLite + SQLAlchemy ORM | `app/database.py` (creates `blog.db`) |
| JWT authentication | `app/security.py`, `app/deps.py` |
| `/auth/register`, `/auth/login` | `app/routers/auth.py` |
| CRUD for posts | `app/routers/posts.py` |
| Comments | `app/routers/comments.py` |
| Likes / unlikes | `app/routers/likes.py` |
| Ownership checks (only owner can update/delete) | `_get_owned_post()` in `app/routers/posts.py` (returns `403 Forbidden`) |
| Public read access (posts + comments) | `GET /posts`, `GET /posts/{id}`, `GET /posts/{id}/comments` have no auth requirement |
| Input validation | Pydantic schemas in `app/schemas.py` (min lengths, `EmailStr`, etc.) |
| Swagger UI | Auto-served at `/docs` (and ReDoc at `/redoc`) |
| `/posts/mine` | `app/routers/posts.py` |
| Email notifications on comment/like | `app/email_utils.py`, called from `comments.py` and `likes.py` via `BackgroundTasks` |

**Note on emails:** No real SMTP credentials were provided in the assignment,
so `send_email_notification()` simulates sending mail by logging the To /
Subject / Body to the console (you'll see it in the terminal running
uvicorn). The function is called from exactly the place a real email would
be sent from. A commented-out `smtplib` block is included in
`app/email_utils.py` — uncomment and fill in your SMTP details if you want
it to send real emails.

---

## 📁 Project structure

```
blog_api/
├── app/
│   ├── main.py          # FastAPI app, includes all routers
│   ├── config.py         # .env-based settings (SMTP, secret key)
│   ├── database.py        # SQLAlchemy engine/session (SQLite)
│   ├── models.py           # User, Post, Comment, Like, SubscriptionPlan, BillingHistory
│   ├── schemas.py          # Pydantic request/response models
│   ├── security.py         # password hashing + JWT create/decode
│   ├── deps.py              # get_current_user dependency
│   ├── plan_limits.py        # subscription plan-limit enforcement
│   ├── invoice_utils.py       # PDF invoice generation
│   ├── media_utils.py          # image upload handling
│   ├── services/
│   │   ├── email_service.py     # SMTP sending — the only module that touches SMTP
│   │   └── notification_service.py  # builds like/comment email content
│   └── routers/
│       ├── auth.py          # /auth/register, /auth/login
│       ├── posts.py          # CRUD + /posts/mine + pagination/search
│       ├── comments.py        # add/list comments (triggers email notification)
│       ├── likes.py            # like/unlike (triggers email notification)
│       └── subscriptions.py     # plans, subscribe, mine, billing-history
├── admin_panel/            # separate Django project — real Django Admin, same blog.db
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🛠 Step 1 — Open the project in VS Code

1. Unzip `blog_api.zip` somewhere on your computer.
2. Open **VS Code**.
3. `File → Open Folder…` and select the unzipped `blog_api` folder.
4. Make sure you have the **Python extension** installed in VS Code
   (Extensions panel → search "Python" → install the Microsoft one).

---

## 🛠 Step 2 — Create a virtual environment & install dependencies

Open a terminal in VS Code: **Terminal → New Terminal**. Then run:

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Mac / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

After activation you should see `(venv)` at the start of your terminal
prompt. In VS Code, also select this environment as your interpreter:
`Ctrl+Shift+P` → "Python: Select Interpreter" → pick the one inside
`venv`.

---

## 🛠 Step 3 — Run the API

```bash
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

This automatically creates a `blog.db` SQLite file (with the `users`,
`posts`, `comments`, `likes` tables) in the project folder the first time
you run it — no manual migration step needed.

Leave this terminal running. This is also where you'll see the simulated
email notification logs when comments/likes happen.

---

## 🛠 Step 4 — Test everything in Swagger UI

Open your browser to:

**http://127.0.0.1:8000/docs**

Suggested test flow:

1. **POST `/auth/register`** — register two users, e.g. `alice` and `bob`
   (click "Try it out", fill the JSON body, Execute).
2. **POST `/auth/login`** — click "Try it out", enter `alice`'s
   username/password, Execute → copy the `access_token` from the response.
   *(Or simpler: click the green **🔓 Authorize** button at the top right
   of the page, type in alice's username/password there, and Swagger
   handles the token for you for every request after that.)*
3. **POST `/posts`** — while authorized as alice, create a post. Fill in
   `title` and `content`, and optionally click "Choose File" next to
   `image` to attach a cover photo.
4. **GET `/posts`** — no auth needed. Try it with query params, e.g.
   `page=1&limit=2` or `search=hello`, to see pagination/search in action.
   Copy the `image_url` from a post's response and open
   `http://127.0.0.1:8000<image_url>` in a new tab to confirm the image
   loads.
5. **Authorize as bob** and try **PUT `/posts/{id}`** or **DELETE
   `/posts/{id}`** on alice's post → you should get `403 Forbidden`
   ("You can only modify your own posts"). This proves ownership checks
   work.
6. **POST `/posts/{id}/comments`** as bob → check the uvicorn terminal,
   you'll see an "EMAIL NOTIFICATION" log addressed to alice.
7. **POST `/posts/{id}/like`** as bob → same thing, a like notification
   log appears. Try liking it again → `400 Bad Request` (already liked).
   **DELETE `/posts/{id}/like`** removes it.
8. **GET `/posts/mine`** while authorized as alice → only alice's posts.

---

## 📸 Step 5 — Screenshots of the SQLite tables

You need a way to *see* the contents of `blog.db`. Two easy options:

### Option A — VS Code extension (recommended, no extra software)
1. In VS Code, go to Extensions and install **"SQLite Viewer"** (by
   `qwtel`) or **"SQLite"** (by `alexcvzz`).
2. In the file explorer, click on `blog.db`.
3. It opens a table view — click on `users`, `posts`, `comments`, `likes`
   one at a time.
4. Take a screenshot of each table (Windows: `Win+Shift+S`, Mac:
   `Cmd+Shift+4`).

### Option B — DB Browser for SQLite (standalone app)
1. Download it free from https://sqlitebrowser.org/
2. Open it → "Open Database" → select `blog.db` from your project folder.
3. Go to the **"Browse Data"** tab, use the table dropdown to switch
   between `users`, `posts`, `comments`, `likes`.
4. Screenshot each one.

### Option C — Quick command line check (to verify data before screenshotting)
```bash
python -c "
import sqlite3
conn = sqlite3.connect('blog.db')
cur = conn.cursor()
for t in ['users','posts','comments','likes']:
    print('---', t, '---')
    cur.execute(f'SELECT * FROM {t}')
    for row in cur.fetchall():
        print(row)
"
```

> 💡 Tip: Do a few register/login/post/comment/like actions in Swagger
> **first**, then open the DB viewer — otherwise the tables will look
> empty.

---

## 🔑 Notes on security / config

* JWT secret key defaults to a placeholder in `app/security.py`. For real
  use, copy `.env.example` to `.env` and set your own `SECRET_KEY`, or set
  it as an OS environment variable before running uvicorn.
* Passwords are hashed with **bcrypt** via `passlib` before being stored —
  the raw password is never saved (see the `password` column in `users`,
  it stores something like `$2b$12$...`, not the plaintext).
* Tokens expire after 24 hours (`ACCESS_TOKEN_EXPIRE_MINUTES` in
  `app/security.py`).

## 🧯 Troubleshooting

* **`ModuleNotFoundError`** → make sure your venv is activated and you ran
  `pip install -r requirements.txt` inside it.
* **Port already in use** → run `uvicorn app.main:app --reload --port 8001`
  instead, and open `http://127.0.0.1:8001/docs`.
* **Swagger "Authorize" button not accepting login** → double check you're
  entering the exact username/password used at registration; `client_id`
  / `client_secret` fields in that dialog can be left blank.
* Delete `blog.db` any time to start with a completely empty database —
  it will be recreated automatically the next time you run the server.
