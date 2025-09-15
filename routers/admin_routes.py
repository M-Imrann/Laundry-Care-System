from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.role_decorator_util import role_required
import dateutil
from services.admin_service import (
    list_all_orders,
    create_order_for_customer,
    add_worker,
    assign_customer_to_worker,
    create_admin
)
from utils.cancel_order_util import cancel_order


# Blueprint for admin-specific routes
admin_bp = Blueprint("admin_bp", __name__)


@admin_bp.route("/orders", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_all_orders(user_id, user_role):
    """
    Retrieve all orders in the system (admin only).

    Args:
        user_id: The ID of the authenticated admin.
        user_role: The role of the user (must be admin).

    Returns:
        Response: JSON list of all orders.
    """
    return list_all_orders()


@admin_bp.route("/create-order", methods=["POST"])
@jwt_required()
@role_required("admin")
def create_order(user_id, user_role):
    """
    Create a new order for a customer (admin only).

    Args:
        user_id: The ID of the authenticated admin.
        user_role: The role of the user (must be admin).

    Returns:
        Response: JSON response with success or error message.
    """
    data = request.json or {}

    # Validate pickup_time and delivery_time format
    try:
        pickup_time = dateutil.parser.isoparse(data.get("pickup_time"))
        delivery_time = dateutil.parser.isoparse(data.get("delivery_time"))
    except Exception:
        return jsonify(
            {
                "error": "pickup_time and delivery_time must"
                "be ISO datetime strings"
            }
        ), 400

    # Extract required fields
    customer_id = data.get("customer_id")
    worker_id = data.get("worker_id")
    price = data.get("price")
    address_id = data.get("address_id")

    # Check required fields
    required = {
        "customer_id": customer_id,
        "worker_id": worker_id,
        "price": price,
        "address_id": address_id
    }
    for field, value in required.items():
        if not value:
            return jsonify({"error": f"{field} is required"}), 400

    return create_order_for_customer(
        customer_id=customer_id,
        worker_id=worker_id,
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        price=float(price),
        created_by=user_id,
        address_id=address_id
    )


@admin_bp.route("/cancel-order/<int:order_id>", methods=["DELETE"])
@jwt_required()
@role_required("admin")
def cancel_order_route(order_id, user_id, user_role):
    """
    Cancel an existing order (admin only).

    Args:
        order_id: The ID of the order to cancel.
        user_id: The ID of the authenticated admin.
        user_role: The role of the user (must be admin).

    Returns:
        Response: JSON response indicating success or failure of cancellation.
    """
    return cancel_order(user_id=user_id, order_id=order_id, role=user_role)


@admin_bp.route("/add-worker", methods=["POST"])
@jwt_required()
@role_required("admin")
def add_worker_route(user_id, user_role):
    """
    Add a new worker to the system (admin only).

    Args:
        user_id: The ID of the authenticated admin.
        user_role: The role of the user (must be admin).

    Returns:
        Response: JSON response with success or error message.
    """
    data = request.json or {}

    name = data["name"]
    email = data["email"]
    phone = data["phone"]
    password = data["password"]

    # Validate required fields
    required = {
        "name": name,
        "email": email,
        "phone": phone,
        "password": password
    }
    for field, value in required.items():
        if not value:
            return jsonify({"error": f"{field} is required"}), 400

    return add_worker(
        name=name,
        email=email,
        phone=phone,
        password=password
    )


@admin_bp.route("/workers/<int:worker_id>/assign_customer", methods=["POST"])
@jwt_required()
@role_required("admin")
def assign_customer(worker_id, user_id, user_role):
    """
    Assign a customer to a worker (admin only).

    Args:
        worker_id: The ID of the worker.
        user_id: The ID of the authenticated admin.
        user_role: The role of the user (must be admin).

    Returns:
        Response: JSON response with success or error message.
    """
    data = request.json or {}
    customer_id = data.get("customer_id")
    if not customer_id:
        return jsonify({"error": "customer_id is required"}), 400

    return assign_customer_to_worker(
        worker_id=worker_id,
        customer_id=customer_id
    )


@admin_bp.route("/add-new-admin", methods=["POST"])
@jwt_required()
@role_required("admin")
def add_admin(user_id, user_role):
    """
    Create a new admin account (admin only).

    Args:
        user_id: The ID of the authenticated admin.
        user_role: The role of the user (must be admin).

    Returns:
        Response: JSON response with success or error message.
    """
    data = request.json or {}

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    phone = data.get("phone")
    role = data.get("role")

    response, status = create_admin(name, email, password, phone, role)

    return jsonify(response), status
