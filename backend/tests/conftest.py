import os
import subprocess
import sys

import pytest

TEST_URL = os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg://localhost:5432/collegefind_test")
# The suite runs `alembic downgrade base` (drops every table). Never allow that against a remote/shared database.
assert "localhost" in TEST_URL or "127.0.0.1" in TEST_URL, "Refusing to run tests against a non-local database"
os.environ["DATABASE_URL"] = TEST_URL  # must be set before app.* is imported
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture(scope="session")
def migrated():
    """Build the schema purely through Alembic so migrations are what's under test."""
    env = {**os.environ, "ALEMBIC_DATABASE_URL": TEST_URL}
    run = lambda *a: subprocess.run([sys.executable, "-m", "alembic", *a], check=True, env=env,
                                    cwd=os.path.dirname(os.path.dirname(__file__)), capture_output=True)
    run("downgrade", "base")
    run("upgrade", "head")
    yield
