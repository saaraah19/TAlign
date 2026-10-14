# Sandbox end-to-end tooling

Why this exists: the normal test suite uses mocked repositories, so it can
never see a bug that only appears against a real database. Running the real
backend on a real Postgres found three such bugs in one afternoon (a 500 on
every "add a recruiter", a 500 on every leave approval/cancel, and a 500 on the
public job list), all variants of async SQLAlchemy's "MissingGreenlet" error.
This folder is the recipe, so it can be repeated after any change that touches
the database layer.

## What you need
- Python 3.11+ with the backend installed (`pip install -e ".[dev]"` in `backend/`)
- A Postgres with the `pgvector` extension. Docker Compose provides one; where
  Docker is not available, `pip install pgserver` bundles Postgres + pgvector.

## Recipe (without Docker)
```bash
pip install pgserver
python - <<'PY'
import pgserver, pathlib
srv = pgserver.get_server(pathlib.Path("/tmp/talign-pg"), cleanup_mode=None)
print(srv.get_uri())          # postgresql://postgres:@/postgres?host=/tmp/talign-pg
PY

export ENVIRONMENT=local DEBUG=true LOG_LEVEL=WARNING
export DATABASE_URL="postgresql+asyncpg://postgres@/postgres?host=/tmp/talign-pg"
export DATABASE_URL_SYNC="postgresql+psycopg2://postgres@/postgres?host=/tmp/talign-pg"
export LOCAL_STORAGE_PATH=/tmp/talign-storage JWT_SECRET_KEY=local-only-secret-0123456789abcdef

cd backend && alembic upgrade head
python ../tools/sandbox_e2e/launcher.py &        # backend on :8000 with stand-in AI
python scripts/seed_demo.py                      # play the demo world through the API
python ../tools/sandbox_e2e/verify_isolation.py  # tenant isolation + permissions
```

## Limits
The AI stand-ins prove plumbing, not quality (see `launcher.py`). Real analysis
scores, drafted emails and Compass answers need a real `GOOGLE_API_KEY`.
