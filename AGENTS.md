# AGENTS.md — my_ai_TA

AI Teaching Assistant (AI 实验报告助手): a Flask learning project where students log in, submit a lab topic, and an LLM generates a structured experiment report (目的/原理/步骤/数据/分析) saved to per-user history.

## Running

- Python environment: project-local venv `./venv` (Python 3.13.9) — activate with `.\venv\Scripts\Activate.ps1`, or call `venv\Scripts\python.exe` / `venv\Scripts\flask.exe` directly. (A conda env `flask_learning` (Python 3.10) was used earlier in the project's history; the venv is what all commands actually run against now.)
- Main app: `python app.py` → dev server at `http://127.0.0.1:5050` (`debug=True`, `host="0.0.0.0"`)
- Prerequisites: local MySQL (db `test_ver1`, root/123456 per `config.py`), `.env` with `PARATERA_API_KEY` (and optionally `SECRET_KEY`)
- DB schema is managed by flask-migrate/Alembic: initial revision `fd11e8ff7437` (creates all 6 tables) was applied via `flask db upgrade` on 2026-10-06. After model changes: `flask db migrate -m "..."` then `flask db upgrade` (in PowerShell set `$env:FLASK_APP = "app.py"` first if needed).
- Redis runs in **WSL** (accessed from Windows at `127.0.0.1:6379`). Optional standalone worker: `python worker.py` (Redis task-queue consumer).

## Critical traps

- **`templates/base.html` is NOT a layout template.** It only loads jQuery; no template extends it. Every page is a fully standalone HTML document with its own `<head>` and CDN links. Do not assume Jinja2 inheritance — global head/nav changes must be applied to each template individually.
- **`practice.py` and `practice_sql.py` are scratch/practice apps**, not part of the main app (their docstrings say so). Never import them from the main app or "fix" them into it. `practice_sql.py` has import-time side effects (inserts MySQL rows, writes Redis).
- **`requirements.txt` is UTF-16 encoded** — `pip install -r requirements.txt` can fail on some systems; re-save as UTF-8 when editing it.
- **DB driver**: `config.py` URI uses `mysql+pymysql://` (fixed 2026-09-30; was `mysql+mysqldb` which requires `mysqlclient` — venv only has PyMySQL, causing `ModuleNotFoundError: No module named 'MySQLdb'` at `db.init_app`). Keep the protocol matching the installed driver.
- **`migrations/` exists and is live** (initial revision `fd11e8ff7437_create_all_tables_with_many_to_many.py`, applied 2026-10-06; `alembic_version` tracks the head). Schema changes must go through `flask db migrate` / `flask db upgrade` — don't hand-edit the DB or fall back to `db.create_all()`.
- **ForeignKey targets must be PK/unique columns.** The secondary table `Reports_AI_Models` originally pointed its FKs at `report.created_at` / `AI_models.assigned_at` (timestamps that don't exist as columns), which made `flask db migrate` die with `NoReferencedColumnError` (fixed 2026-10-01). FKs now target `report.id` / `AI_models.model_number`; `assigned_at` is a plain DateTime column on the secondary table, not a FK target.

## Architecture

- `app.py` — entry point: creates app, loads `config.py`, binds `db`/`migrate`, registers 5 blueprints.
- `models.py` — **all models and `db`/`migrate` extensions live here** (documented pattern to avoid circular imports). Route files must import `db`, `User`, `Report`, etc. from `models`, never define models elsewhere. Models: `User`, `Report`, `Admin`, `Permission`, `AI_Models` plus the `Reports_AI_Models` secondary `Table`. Key points: `Report.created_at` is a real DateTime column (`default=datetime.now`) that `history_routes` orders by; many-to-many is `Report.ai_models` ↔ `AI_Models.reports` through the secondary table (call time lives in its `assigned_at` column); `Base` uses a `naming_convention` MetaData so Alembic generates named constraints.
- `routes/` — one blueprint per file: `main_routes.py` (`/`, calls AI + saves Report), `AI_client_routes.py` (`/read` POST, file-upload AI reading with dual-model split), `history_routes.py` (`/history`, last 10 reports), `login_routes.py` (`/login`, `/register`), `tutorial_routes.py` (`/tutorial`, JSON echo playground).
- `routes/AI_client_routes.py` — blueprint `AI_client_bp` with `url_prefix='/read'` (route is `/read/` POST). **Model division of labor lives here**: text files (pdf/docx/pptx) → `DeepSeek-V4-Pro`; images (jpg/png/tiff/bmp) → `MiniMax-M3` (vision, receives base64 `image_url` data URLs). Renders results back into `index.html`. Imports `AI_Models` for a planned (commented-out) `save()` that would record which model generated a paragraph — the sketch still references the old pre-fix API and must be rewritten against `Report.ai_models` if revived.
- `file_reader.py` — file-parsing module exposing `extract_file_content(FileStorage)`; returns `{kind: text|image|error, ...}` dicts. pdf/docx/pptx → extracted text (capped at 20000 chars), images → base64 + mime. Parsing failures return per-file error entries instead of raising.
- `ai_client.py` — module-level OpenAI SDK client pointed at Paratera (`https://llmapi.paratera.com/v1/`); shared by all blueprints. Models used across the app: `DeepSeek-V4-Pro` (text), `MiniMax-M3` (vision). Called synchronously inside route POST handlers.
- `worker.py` — Redis queue consumer skeleton; task processing body is intentionally empty.

## Conventions

- **Comments and docstrings are in Chinese; identifiers are in English.** Keep this mix.
- **SQLAlchemy 2.0 typed style only**: `Mapped[...]` / `mapped_column(...)`, `db.session.scalar(db.select(...))`, `db.session.scalars(...).all()`. Never use legacy `Model.query`.
- **Auth is manual Flask sessions** (no Flask-Login): `session["user_id"]`, `session["user_type"]`, `session["is_login"]`. Protect routes by checking `session.get("is_login")` and redirecting to `url_for("login.login")` (see `history_routes.py`). Passwords via `werkzeug.security` hash/verify. Note: `user_type` is never persisted to the DB.
- **Forms are classic full-page POSTs** rendered server-side; errors are passed to templates as context (`render_template(..., error=...)`). No AJAX/fetch, no CSRF tokens, no flash messages — match this pattern unless asked otherwise.
- **Frontend**: Bootstrap via jsDelivr CDN (version drift exists: 5.3.0-alpha1 on index/history, 5.3.3 on login/register). Static files referenced via `{{ url_for('static', filename='...') }}`.
- Config values (DB creds) are hardcoded in `config.py`; secrets come from `.env` via `python-dotenv`.

## Known issues (don't "fix" unless asked)

- `history.html` loads `base.css` via a `<script>` tag (styles don't apply) and is missing `</html>`.
- `static/register.js` is empty; jQuery in `static/` is effectively unused.
- No logout route, no CSRF protection, `debug=True` with `host="0.0.0.0"`.
- The AI call in `index()` is blocking with no error handling.
