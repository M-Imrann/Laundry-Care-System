import pytest
from unittest.mock import patch
from flask import Flask, jsonify
from flask_jwt_extended import create_access_token, JWTManager
from routers.worker_routes import worker_bp
from models import UserRole
import datetime
from datetime import timezone


# ---------------------
# Fixtures
# ---------------------
@pytest.fixture
def app():
    """
    Create and configure a Flask app instance for testing.

    - Registers the worker blueprint
    - Sets up JWT for authentication
    """
    flask_app = Flask(__name__)
    flask_app.config["JWT_SECRET_KEY"] = "test-secret"

    # Register worker routes
    flask_app.register_blueprint(worker_bp, url_prefix="/worker")

    # Initialize JWT Manager
    JWTManager(flask_app)
    return flask_app


@pytest.fixture
def client(app):
    """
    Fixture to provide Flask test client.
    """
    return app.test_client()


def get_auth_header(app, role: str = "worker", user_id: int = 2) -> dict:
    """
    Generate Authorization header with JWT token for testing.

    Args:
        app: Flask app instance
        role: Role of the user (default: 'worker')
        user_id: ID of the user (default: 2)

    Returns:
        dict: Authorization header containing the JWT token
    """
    token = create_access_token(
        identity=str(user_id),
        additional_claims={"role": UserRole[role].value}
    )
    return {"Authorization": f"Bearer {token}"}


@patch("routers.worker_routes.list_unclaimed_orders")
def test_get_unclaimed_orders_success(
    mock_list_unclaimed_orders, client, app
):
    """
    Testcase that Worker fetches unclaimed orders successfully.
    """
    mock_list_unclaimed_orders.return_value = (jsonify([{"order_id": 1}]), 200)

    response = client.get(
        "/worker/orders/unclaimed",
        headers=get_auth_header(app),
    )

    assert response.status_code == 200
    assert response.get_json()[0]["order_id"] == 1
    mock_list_unclaimed_orders.assert_called_once()


@patch("routers.worker_routes.claim_order")
def test_claim_order_success(mock_claim_order, client, app):
    """
    Testcase that Worker claims an order successfully.
    """
    mock_claim_order.return_value = (jsonify({"message": "claimed"}), 200)

    response = client.post(
        "/worker/orders/5/claim",
        headers=get_auth_header(app),
    )

    assert response.status_code == 200
    assert response.get_json()["message"] == "claimed"
    mock_claim_order.assert_called_once_with(worker_id=2, order_id=5)


@patch("routers.worker_routes.update_order_status")
def test_update_order_status_success(mock_update_order_status, client, app):
    """
    Testcase that Worker updates order status successfully.
    """
    mock_update_order_status.return_value = (
        jsonify({"message": "updated"}), 200
    )

    response = client.post(
        "/worker/orders/10/status",
        json={"status": "delivered"},
        headers=get_auth_header(app),
    )

    assert response.status_code == 200
    assert response.get_json()["message"] == "updated"
    mock_update_order_status.assert_called_once_with(
        worker_id=2,
        order_id=10,
        status="delivered",
    )


def test_update_order_status_missing_field(client, app):
    """
    Testcase that Worker updates order status with missing
    `status` field (should fail).
    """
    response = client.post(
        "/worker/orders/10/status",
        json={},  # Missing status field
        headers=get_auth_header(app),
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Status is required"


@patch("routers.worker_routes.create_order_for_customer")
def test_worker_create_order_success(
    mock_create_order_for_customer, client, app
):
    """
    Testcase that Worker creates an order for a customer successfully.
    """
    mock_create_order_for_customer.return_value = (
        jsonify({"message": "created"}), 201
    )

    payload = {
        "pickup_time": datetime.datetime.now(timezone.utc).isoformat(),
        "delivery_time": (
            datetime.datetime.now(timezone.utc)
            + datetime.timedelta(hours=2)
        ).isoformat(),
        "customer_id": 5,
        "price": 150,
    }

    response = client.post(
        "/worker/create-order",
        json=payload,
        headers=get_auth_header(app),
    )

    assert response.status_code == 201
    assert response.get_json()["message"] == "created"
    mock_create_order_for_customer.assert_called_once()


def test_worker_create_order_invalid_iso(client, app):
    """
    Testcase that Worker provides invalid ISO datetime for order
    creation (should fail).
    """
    payload = {
        "pickup_time": "invalid",
        "delivery_time": "invalid",
        "customer_id": 1,
        "price": 100,
    }

    response = client.post(
        "/worker/create-order",
        json=payload,
        headers=get_auth_header(app),
    )

    assert response.status_code == 400
    assert "ISO datetime" in response.get_json()["error"]


def test_worker_create_order_missing_fields(client, app):
    """
    Testcase that Worker omits required fields (customer_id, price)
    in order creation (should fail).
    """
    payload = {
        "pickup_time": datetime.datetime.now(timezone.utc).isoformat(),
        "delivery_time": (
            datetime.datetime.now(timezone.utc)
            + datetime.timedelta(hours=2)
        ).isoformat(),
        # Missing customer_id and price
    }

    response = client.post(
        "/worker/create-order",
        json=payload,
        headers=get_auth_header(app),
    )

    assert response.status_code == 400
    assert "customer_id and price" in response.get_json()["error"]
