import pytest
from app import create_app
from database import db


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
def client(app):
    """
    Provide a test client for the Flask app.
    """
    return app.test_client()


def test_app_creation(app):
    """
    Ensure the Flask app is created successfully
    and the testing config is enabled.
    """
    assert app is not None
    assert app.config["TESTING"] is True


def test_blueprints_registered(app):
    """
    Verify that all expected blueprints are registered.
    """
    expected_blueprints = {"auth", "customer", "worker", "admin"}
    assert expected_blueprints.issubset(app.blueprints.keys())
