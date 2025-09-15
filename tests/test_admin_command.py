import pytest
from click.testing import CliRunner
from admin_command import create_admin
from models import db, User, UserRole
from app import create_app


@pytest.fixture
def app():
    """
    Create and configure a Flask app instance for testing
    with an in-memory SQLite database.
    """
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def runner(app):
    """
    Provide a Click CLI runner for invoking commands.
    """
    return CliRunner()


@pytest.fixture(autouse=True)
def app_context(app):
    """
    Automatically push/pop an application context for each test.
    """
    with app.app_context():
        yield


def test_create_admin_success(runner):
    """
    Test successful creation of a new admin via CLI command.
    """
    result = runner.invoke(
        create_admin,
        [
            "Test Admin",
            "test@example.com",
            "password123",
            "1234567890",
            "admin",
        ],
    )

    user = User.query.filter_by(email="test@example.com").first()

    assert result.exit_code == 0
    assert "Admin 'test@example.com' created successfully." in result.output
    assert user is not None
    assert user.role == UserRole.admin


def test_create_admin_existing_user(runner):
    """
    Test creating an admin when the user already exists.
    Should return a 'user exists' message instead.
    """
    # Pre-insert a user into the database
    db.session.add(
        User(
            name="Existing",
            email="exist@example.com",
            password="pass",
            phone="123",
            role=UserRole.admin,
        )
    )
    db.session.commit()

    result = runner.invoke(
        create_admin,
        [
            "Existing",
            "exist@example.com",
            "password123",
            "1234567890",
            "admin",
        ],
    )

    assert result.exit_code == 0
    assert "User 'exist@example.com' already exists." in result.output
