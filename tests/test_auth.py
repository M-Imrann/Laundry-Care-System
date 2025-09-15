import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
from werkzeug.security import check_password_hash
from unittest.mock import patch, MagicMock

from routers.auth_routes import auth_bp
from services.auth_service import (
    create_user,
    login_user,
    hash_password,
    check_password,
    generate_access_token,
)
from utils import validators_util
from utils.exceptions_util import (
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
)


class DummyRole:
    """
    A dummy role class to mimic Enum behavior in tests.
    """

    def __init__(self, value: str):
        self.value = value


def mock_user_instance(password: str = "Strong@123", role: str = "customer"):
    """
    Return a mock user object with hashed password and dummy role.
    """
    user = MagicMock()
    user.id = 1
    user.email = "example@test.com"
    user.password = hash_password(password)
    user.name = "Test"
    user.role = DummyRole(role)
    return user


@pytest.fixture
def app():
    """
    Return a Flask app with JWT and auth blueprint registered.
    """
    flask_app = Flask(__name__)
    flask_app.config["JWT_SECRET_KEY"] = "test-secret"
    flask_app.register_blueprint(auth_bp, url_prefix="/auth")
    JWTManager(flask_app)
    return flask_app


@pytest.fixture
def app_context(app):
    """
    Automatically push an app context for tests.
    """
    with app.app_context():
        yield


@pytest.fixture
def client(app):
    """
    Provide a Flask test client.
    """
    return app.test_client()


@pytest.fixture
def valid_payload():
    """
    Provide a valid payload for creating a user.
    """
    return {
        "name": "Test",
        "email": "test@test.com",
        "phone": "+12345678901",
        "role": "customer",
        "password": "Strong@123",
    }


def test_signup_route(client):
    """
    Test signup endpoint success and failure.
    """
    with patch("routers.auth_routes.create_user", return_value=("ok", 201)):
        response = client.post(
            "/auth/signup",
            json={"email": "signup@test.com"}
            )
        assert response.status_code == 201

    response = client.post("/auth/signup", json={})
    assert response.status_code == 400
    assert b"Input Payload is required" in response.data


def test_login_route(client):
    """
    Test login endpoint success and failure.
    """
    with patch("routers.auth_routes.login_user", return_value=("ok", 200)):
        response = client.post(
            "/auth/login",
            json={"email": "example@test.com", "password": "Pass@123"},
        )
        assert response.status_code == 200

    response = client.post("/auth/login", json={"email": ""})
    assert response.status_code == 400
    assert b"Email is required" in response.data


def test_password_helpers():
    """
    Test password hashing and validation.
    """
    raw_password = "Strong@123"
    hashed_password = hash_password(raw_password)

    assert check_password_hash(hashed_password, raw_password)
    assert check_password(raw_password, hashed_password)
    assert not check_password("wrong", hashed_password)


def test_generate_access_token(app_context):
    """
    Test JWT token generation.
    """
    token = generate_access_token(1, "customer")
    assert isinstance(token, str)


@patch("services.auth_service.db.session")
@patch("services.auth_service.User")
def test_create_user_success(mock_user, mock_db, valid_payload, app_context):
    """
    Test successful user creation with valid payload.
    """
    mock_user_instance_obj = MagicMock()
    mock_user_instance_obj.id = 1
    mock_user.return_value = mock_user_instance_obj

    # No existing user
    mock_user.query.filter_by.return_value.first.return_value = None

    # Mock DB methods
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.flush.return_value = None

    with patch("services.auth_service.UserRole") as mock_role:
        mock_role.customer = DummyRole("customer")
        mock_role.worker = DummyRole("worker")
        mock_role.__getitem__.side_effect = lambda key: DummyRole(key)

        with patch(
            "services.auth_service.validate_email",
            return_value=valid_payload["email"],
        ), patch(
            "services.auth_service.validate_phone",
            return_value=valid_payload["phone"],
        ), patch(
            "services.auth_service.validate_password",
            return_value=valid_payload["password"],
        ), patch("services.auth_service.Customer"), patch(
            "services.auth_service.Worker"
        ):
            response, status = create_user(valid_payload)
            assert status == 201
            assert b"User created successfully" in response.data


@pytest.mark.parametrize(
    "exception,expected_status",
    [
        (ValidationError("bad email", field="email"), 400),
        (AuthenticationError("bad auth"), 403),
        (AuthorizationError("unauthorized"), 403),
        (NotFoundError("missing"), 404),
        (Exception("boom"), 500),
    ],
)
def test_create_user_exceptions(
    valid_payload, app_context, exception, expected_status
):
    """
    Test user creation error handling for multiple exceptions.
    """
    with patch(
        "services.auth_service.validate_email",
        side_effect=exception,
    ):
        response, status = create_user(valid_payload)
        assert status == expected_status


def test_login_user_service(app_context):
    """
    Test login_user service with valid and invalid scenarios.
    """
    with patch("services.auth_service.User") as mock_user:
        mock_user.query.filter_by.return_value.first.side_effect = [
            None,                              # invalid email
            mock_user_instance("Strong@123"),  # valid login
            mock_user_instance("Strong@123"),  # wrong password
        ]

        # Invalid email
        response, status = login_user("invalid@test.com", "Pass@123")
        assert status == 401

        # Success
        response, status = login_user("example@test.com", "Strong@123")
        assert status == 200
        assert b"Login successful" in response.data

        # Wrong password
        response, status = login_user("example@test.com", "WrongPass")
        assert status == 401
        assert b"Invalid password" in response.data


@pytest.mark.parametrize("email", ["bademail", "anotherbad@com"])
def test_validate_email_invalid(email):
    """
    Invalid emails should raise ValidationError.
    """
    with pytest.raises(ValidationError) as exc_info:
        validators_util.validate_email(email)
    assert "Invalid email format" in str(exc_info.value)


def test_validate_email_duplicate(monkeypatch):
    """
    Duplicate emails should raise ValidationError.
    """
    monkeypatch.setattr(
        "utils.validators_util.User",
        MagicMock(
            query=MagicMock(
                filter_by=lambda **_: MagicMock(first=lambda: True)
            )
        ),
    )
    with pytest.raises(ValidationError) as exc_info:
        validators_util.validate_email("test@test.com")
    assert "Email already exists" in str(exc_info.value)


def test_validate_password_invalid():
    """
    Weak password should raise ValidationError.
    """
    with pytest.raises(ValidationError) as exc_info:
        validators_util.validate_password("weak")
    assert "Password must be at least" in str(exc_info.value)


@pytest.mark.parametrize("phone", ["12345", "+12"])
def test_validate_phone_invalid(phone):
    """
    Invalid phone numbers should raise ValidationError.
    """
    with pytest.raises(ValidationError) as exc_info:
        validators_util.validate_phone(phone)
    assert "Invalid phone number format" in str(exc_info.value)


def test_validate_phone_duplicate(monkeypatch):
    """
    Duplicate phone numbers should raise ValidationError.
    """
    monkeypatch.setattr(
        "utils.validators_util.User",
        MagicMock(
            query=MagicMock(
                filter_by=lambda **_: MagicMock(first=lambda: True)
            )
        ),
    )
    with pytest.raises(ValidationError) as exc_info:
        validators_util.validate_phone("+12345678901")
    assert "Phone number already exists" in str(exc_info.value)


def test_validation_error_to_dict():
    """
    ValidationError should convert to dict properly.
    """
    error = ValidationError("bad", field="email")
    assert error.to_dict() == {"error": "bad", "field": "email"}


@pytest.mark.parametrize(
    "exception_cls,message",
    [
        (AuthenticationError, "invalid"),
        (AuthorizationError, "unauthorized"),
        (NotFoundError, "missing"),
    ],
)
def test_custom_exceptions(exception_cls, message):
    """
    Custom exceptions should include their messages in string repr.
    """
    error = exception_cls(message)
    assert message in str(error)
