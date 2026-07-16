# Task Manager REST API

A lightweight, JWT-authenticated REST API for managing personal tasks, built with **Flask**. Each user registers/logs in, receives a JWT, and can then create, read, update, and delete their own tasks — other users' tasks are never visible to them.

Built as a demonstration of backend fundamentals: REST API design, authentication, database integration, input validation, and automated testing.

## Features

- User registration & login with hashed passwords (`werkzeug.security`)
- Stateless authentication via **JWT** (`PyJWT`), with token expiry
- Full CRUD REST API for tasks, scoped per authenticated user
- Optional filtering of tasks by status (`?status=pending`)
- Input validation with clear JSON error responses and proper HTTP status codes
- SQLite persistence via raw SQL (`sqlite3`) — the data-access layer (`app/db.py`) is intentionally isolated so it can be swapped for **MySQL** (`mysql-connector-python`) or **PostgreSQL** (`psycopg2`) by changing one file
- Automated test suite (9 tests) covering auth, CRUD, validation, and cross-user access control
- Flask application factory pattern with blueprints for clean project structure

## Tech Stack

`Python` · `Flask` · `PyJWT` · `SQLite` (swappable for MySQL/PostgreSQL) · `unittest`

## Project Structure

```
task-manager-api/
├── app/
│   ├── __init__.py        # Application factory
│   ├── db.py               # Database connection & schema (swap point for MySQL/Postgres)
│   ├── auth_utils.py        # JWT generation, decoding, and @token_required decorator
│   └── routes/
│       ├── auth.py          # /api/auth/register, /api/auth/login
│       └── tasks.py         # /api/tasks CRUD endpoints
├── tests/
│   └── test_app.py          # Automated test suite
├── run.py                   # Dev server entry point
├── requirements.txt
├── .env.example
└── README.md
```

## Getting Started

### 1. Clone and set up a virtual environment

```bash
git clone <your-repo-url>
cd task-manager-api
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables (optional)

```bash
cp .env.example .env
# edit SECRET_KEY to a long random string before deploying anywhere real
```

### 4. Run the app

```bash
python run.py
```

The API will be available at `http://127.0.0.1:5000`.

### 5. Run the tests

```bash
python -m unittest discover -s tests -v
```

## API Reference

### Auth

| Method | Endpoint             | Description                  | Auth required |
|--------|-----------------------|-------------------------------|----------------|
| POST   | `/api/auth/register`  | Create a new user account      | No             |
| POST   | `/api/auth/login`     | Log in and receive a JWT        | No             |

**Register / Login request body:**
```json
{ "email": "user@example.com", "password": "yourpassword" }
```

**Response:**
```json
{ "message": "Login successful", "token": "eyJhbGciOi..." }
```

Include the token on all task endpoints as:
```
Authorization: Bearer <token>
```

### Tasks

| Method | Endpoint            | Description                              |
|--------|----------------------|--------------------------------------------|
| GET    | `/api/tasks`          | List the authenticated user's tasks (supports `?status=`) |
| POST   | `/api/tasks`          | Create a new task                            |
| GET    | `/api/tasks/<id>`     | Get a single task                            |
| PUT    | `/api/tasks/<id>`     | Update a task                                |
| DELETE | `/api/tasks/<id>`     | Delete a task                                |

**Create/Update task body:**
```json
{ "title": "Write README", "description": "Document the API", "status": "in_progress" }
```
Valid `status` values: `pending`, `in_progress`, `completed`.

### Example curl session

```bash
# Register
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secret123"}'

# Login
TOKEN=$(curl -s -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secret123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

# Create a task
curl -X POST http://127.0.0.1:5000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"Write README","status":"in_progress"}'

# List tasks
curl http://127.0.0.1:5000/api/tasks -H "Authorization: Bearer $TOKEN"
```

## Design Notes

- **Why raw SQL instead of an ORM?** To keep the project dependency-light and to clearly demonstrate direct database integration and query-writing skills. `app/db.py` is the single point of contact with the database, so switching engines only means changing the connection logic and a few placeholder styles (`?` → `%s`), not the routes.
- **Why JWT?** Keeps the API stateless — no server-side session storage needed, which fits a horizontally-scalable REST API.
- **Security:** passwords are hashed with Werkzeug's `generate_password_hash`/`check_password_hash` (PBKDF2); tokens expire after a configurable window (`JWT_EXPIRES_MINUTES`).

## Possible Extensions

- Swap SQLite for PostgreSQL/MySQL in production
- Add pagination to `GET /api/tasks`
- Add refresh tokens
- Dockerize with a `docker-compose.yml` for app + database

## License

MIT
