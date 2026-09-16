# Blog Management API (FastAPI)

A mini blogging system built with **FastAPI + SQLAlchemy + SQLite**.
Authenticated users (JWT) can create/update/delete their own posts (with an
optional cover image), comment on posts, like/unlike posts, browse a
paginated/searchable feed, and email notifications are triggered on new
comments and likes.

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
│   ├── database.py       # SQLAlchemy engine/session (SQLite)
│   ├── models.py          # User, Post, Comment, Like tables
│   ├── schemas.py         # Pydantic request/response models
│   ├── security.py        # password hashing + JWT create/decode
│   ├── deps.py             # get_current_user dependency
│   ├── email_utils.py      # email notification helper
│   └── routers/
│       ├── auth.py          # /auth/register, /auth/login
│       ├── posts.py          # CRUD + /posts/mine
│       ├── comments.py        # add/list comments
│       └── likes.py            # like/unlike
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
