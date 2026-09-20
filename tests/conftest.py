import os
import pytest
from starlette.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set testing environment variables before importing app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-length-long-xyz"
os.environ["AUTO_SEED"] = "false"
os.environ["SMTP_HOST"] = ""

from app.database import Base, get_db
from app.main import app
from app.config import settings
from app.models.user import User
from app.auth.security import hash_password, create_session_token
from app.email.service import outbox

# Use in-memory SQLite for fast, isolated tests
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def db_session():
    connection = TEST_ENGINE.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    outbox.clear()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session):
    user = db_session.query(User).filter(User.email == "testadmin@example.com").first()
    if not user:
        user = User(
            email="testadmin@example.com",
            password_hash=hash_password("adminSecret123!"),
            role="admin",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def admin_headers(admin_user):
    token = create_session_token({"user_id": admin_user.id, "email": admin_user.email, "role": admin_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_cookies(admin_user):
    token = create_session_token({"user_id": admin_user.id, "email": admin_user.email, "role": admin_user.role})
    return {settings.SESSION_COOKIE_NAME: token}
