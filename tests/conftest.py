import os
import tempfile
import pytest

from src import app, db


@pytest.fixture
def client():
    # Use a temporary SQLite DB for tests
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        WTF_CSRF_ENABLED=False,
        LOGIN_DISABLED=False,
    )

    with app.app_context():
        db.create_all()

    with app.test_client() as client:
        yield client

    # Teardown
    with app.app_context():
        db.drop_all()
    try:
        os.remove(db_path)
    except FileNotFoundError:
        pass
