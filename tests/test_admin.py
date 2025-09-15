import pytest
from unittest.mock import patch
from flask import Flask, jsonify
from flask_jwt_extended import create_access_token, JWTManager
from routers.admin_routes import admin_bp
from models import UserRole
import datetime
from datetime import timezone, timedelta


@pytest.fixture
def app():
    """
    Create and configure a Flask app instance for testing.
    """
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.register_blueprint(admin_bp, url_prefix="/admin")
    JWTManager(app)
    return app


@pytest.fixture
def client(app):
    """
    Provide a test client for the Flask app.
    """
    return app.test_client()


def auth_header(app, role: str = "admin", user_id: int = 99) -> dict:
    """
    Generate an authorization header with a JWT token.

    Args:
        app: Flask app instance.
        role: User role (default: "admin").
        user_id: Test user ID (default: 99).

    Returns:
        dict: Authorization header with Bearer token.
    """
    token = create_access_token(
        identity=str(user_id),
        additional_claims={"role": UserRole[role].value},
    )
    return {"Authorization": f"Bearer {token}"}


@patch("routers.admin_routes.list_all_orders")
def test_get_all_orders_success(mock_list, client, app):
    """
    Test retrieving all orders successfully.
    """
    mock_list.return_value = (jsonify([{"order_id": 1}]), 200)

    resp = client.get("/admin/orders", headers=auth_header(app))

    assert resp.status_code == 200
    assert resp.get_json()[0]["order_id"] == 1
    mock_list.assert_called_once()


@patch("routers.admin_routes.create_order_for_customer")
def test_create_order_success(mock_create, client, app):
    """
    Test creating an order successfully.
    """
    mock_create.return_value = (jsonify({"message": "ok"}), 201)

    payload = {
        "pickup_time": datetime.datetime.now(timezone.utc).isoformat(),
        "delivery_time": (
            datetime.datetime.now(timezone.utc) + timedelta(hours=2)
            ).isoformat(),
        "customer_id": 1,
        "worker_id": 2,
        "price": 100,
        "address_id": 10,
    }

    resp = client.post(
        "/admin/create-order",
        json=payload,
        headers=auth_header(app)
        )

    assert resp.status_code == 201
    mock_create.assert_called_once()


def test_create_order_missing_fields(client, app):
    """
    Test order creation with missing fields should return 400.
    """
    payload = {
        "pickup_time": datetime.datetime.now(timezone.utc).isoformat(),
        "delivery_time": (
            datetime.datetime.now(timezone.utc) + timedelta(hours=2)
            ).isoformat(),
        # Missing: customer_id, worker_id, price, address_id
    }

    resp = client.post(
        "/admin/create-order",
        json=payload,
        headers=auth_header(app)
        )

    assert resp.status_code == 400
    assert "customer_id" in resp.get_json()["error"]


def test_create_order_invalid_iso(client, app):
    """
    Test order creation with invalid datetime format should return 400.
    """
    payload = {
        "pickup_time": "bad",
        "delivery_time": "bad",
        "customer_id": 1,
        "worker_id": 2,
        "price": 100,
        "address_id": 1,
    }

    resp = client.post(
        "/admin/create-order",
        json=payload,
        headers=auth_header(app)
        )

    assert resp.status_code == 400
    assert "ISO datetime" in resp.get_json()["error"]


@patch("routers.admin_routes.add_worker")
def test_add_worker_success(mock_add, client, app):
    """
    Test successfully adding a worker.
    """
    mock_add.return_value = (jsonify({"message": "worker added"}), 201)

    payload = {
        "name": "Woker",
        "email": "worker@test.com",
        "phone": "1234567890",
        "password": "Pass@123",
    }

    resp = client.post(
        "/admin/add-worker",
        json=payload,
        headers=auth_header(app)
        )

    assert resp.status_code == 201
    mock_add.assert_called_once()


@patch("routers.admin_routes.assign_customer_to_worker")
def test_assign_customer_success(mock_assign, client, app):
    """
    Test successfully assigning a customer to a worker.
    """
    mock_assign.return_value = (jsonify({"message": "assigned"}), 200)

    payload = {"customer_id": 10}

    resp = client.post(
        "/admin/workers/2/assign_customer",
        json=payload,
        headers=auth_header(app),
    )

    assert resp.status_code == 200
    assert resp.get_json()["message"] == "assigned"
    mock_assign.assert_called_once_with(worker_id=2, customer_id=10)


def test_assign_customer_missing_field(client, app):
    """
    Test assigning a customer with missing fields should return 400.
    """
    resp = client.post(
        "/admin/workers/2/assign_customer",
        json={},
        headers=auth_header(app),
    )

    assert resp.status_code == 400
    assert "customer_id" in resp.get_json()["error"]


@patch("routers.admin_routes.create_admin")
def test_add_admin_success(mock_create, client, app):
    """
    Test successfully adding a new admin.
    """
    mock_create.return_value = ({"message": "admin created"}, 201)

    payload = {
        "name": "Admin",
        "email": "admin@test.com",
        "password": "Pass@123",
        "phone": "123",
        "role": "admin",
    }

    resp = client.post(
        "/admin/add-new-admin",
        json=payload,
        headers=auth_header(app)
        )

    assert resp.status_code == 201
    assert resp.get_json()["message"] == "admin created"
    mock_create.assert_called_once_with(
        "Admin",
        "admin@test.com",
        "Pass@123",
        "123",
        "admin"
        )
