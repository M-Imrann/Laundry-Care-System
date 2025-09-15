import pytest
from unittest.mock import patch
from flask import Flask, jsonify
from flask_jwt_extended import create_access_token, JWTManager
from routers.customer_routes import customer_bp
from models import UserRole
import datetime
from datetime import timezone


@pytest.fixture
def app():
    """
    Create and configure a Flask app instance for testing.

    - Registers the customer blueprint
    - Sets up JWT for authentication
    """
    flask_app = Flask(__name__)
    flask_app.config["JWT_SECRET_KEY"] = "test-secret"

    # Register customer routes
    flask_app.register_blueprint(customer_bp, url_prefix="/customer")

    # Initialize JWT Manager
    JWTManager(flask_app)
    return flask_app


@pytest.fixture
def client(app):
    """
    Fixture to provide Flask test client.
    """
    return app.test_client()


def get_auth_header(app, role: str = "customer", user_id: int = 1) -> dict:
    """
    Generate Authorization header with JWT token for testing.

    Args:
        app: Flask app instance
        role: Role of the user (default: 'customer')
        user_id: ID of the user (default: 1)

    Returns:
        dict: Authorization header containing the JWT token
    """
    token = create_access_token(
        identity=str(user_id),
        additional_claims={"role": UserRole[role].value},
    )
    return {"Authorization": f"Bearer {token}"}


@patch("routers.customer_routes.create_customer_address")
def test_add_address_success(mock_create, client, app):
    """
    Testcase that Customer adds an address successfully.
    """
    mock_create.return_value = (jsonify({"message": "ok"}), 201)

    response = client.post(
        "/customer/address",
        json={"street": "Street 1", "city": "Lahore"},
        headers=get_auth_header(app),
    )

    assert response.status_code == 201
    mock_create.assert_called_once()


def test_add_address_missing_fields(client, app):
    """
    Testcase that Customer adds an address with missing fields (should fail).
    """
    response = client.post(
        "/customer/address",
        json={"street": ""},
        headers=get_auth_header(app),
    )

    assert response.status_code == 400
    assert response.get_json()["field"] == "street"


@patch("routers.customer_routes.create_order_for_customer")
def test_create_order_success(mock_create, client, app):
    """
    Testcase that Customer creates an order successfully.
    """
    mock_create.return_value = (jsonify({"message": "created"}), 201)

    payload = {
        "pickup_time": datetime.datetime.now(timezone.utc).isoformat(),
        "delivery_time": (
            datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=2)
        ).isoformat(),
        "price": 100,
        "address_id": 1,
    }

    response = client.post(
        "/customer/create-order",
        json=payload,
        headers=get_auth_header(app),
    )

    assert response.status_code == 201
    mock_create.assert_called_once()


def test_create_order_invalid_iso(client, app):
    """
    Testcase that Customer provides invalid ISO datetime (should fail).
    """
    payload = {
        "pickup_time": "invalid",
        "delivery_time": "invalid",
    }

    response = client.post(
        "/customer/create-order",
        json=payload,
        headers=get_auth_header(app),
    )

    assert response.status_code == 400
    assert "ISO datetime" in response.get_json()["error"]


def test_create_order_missing_field(client, app):
    """
    Testcase that Customer omits required fields (should fail).
    """
    payload = {
        "pickup_time": datetime.datetime.now(timezone.utc).isoformat(),
        "delivery_time": (
            datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=2)
        ).isoformat(),
        # Missing address_id
    }

    response = client.post(
        "/customer/create-order",
        json=payload,
        headers=get_auth_header(app),
    )

    assert response.status_code == 400
    assert response.get_json()["field"] == "address_id"


@patch("routers.customer_routes.list_customer_orders")
def test_list_orders_success(mock_list, client, app):
    """
    Testcase that Customer lists their orders successfully.
    """
    mock_list.return_value = (jsonify([{"order_id": 1}]), 200)

    response = client.get(
        "/customer/list-orders",
        headers=get_auth_header(app),
    )

    assert response.status_code == 200
    assert response.get_json()[0]["order_id"] == 1
    mock_list.assert_called_once()


@patch("routers.customer_routes.cancel_order")
def test_cancel_order_success(mock_cancel, client, app):
    """
    Testcase that Customer cancels an order successfully.
    """
    mock_cancel.return_value = (jsonify({"message": "cancelled"}), 200)

    response = client.delete(
        "/customer/cancel-order/1",
        headers=get_auth_header(app),
    )

    assert response.status_code == 200
    assert response.get_json()["message"] == "cancelled"
    mock_cancel.assert_called_once()


@patch("routers.customer_routes.cancel_order")
def test_cancel_order_failure(mock_cancel, client, app):
    """
    Testcase that Cancelling an order fails due to internal error.
    """
    mock_cancel.side_effect = Exception("Some error")

    response = client.delete(
        "/customer/cancel-order/1",
        headers=get_auth_header(app),
    )

    assert response.status_code == 400
    assert "error" in response.get_json()
