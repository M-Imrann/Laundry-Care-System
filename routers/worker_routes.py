from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.role_decorator_util import role_required
import dateutil
from services.worker_service import (
    list_unclaimed_orders,
    claim_order,
    update_order_status,
    create_order_for_customer
)


# Blueprint for worker-specific routes
worker_bp = Blueprint("worker_bp", __name__)


@worker_bp.route("/orders/unclaimed", methods=["GET"])
@jwt_required()
@role_required("worker")
def get_unclaimed_orders(user_id, user_role):
    """
    Retrieve all unclaimed orders available for workers.

    Returns:
        JSON response with a list of unclaimed orders.
    """
    return list_unclaimed_orders()


@worker_bp.route("/orders/<int:order_id>/claim", methods=["POST"])
@jwt_required()
@role_required("worker")
def claim_order_route(order_id, user_id, user_role):
    """
    Claim an order for the worker.

    Args:
        order_id: The ID of the order to be claimed.

    Returns:
        JSON response confirming the claim or an error message.
    """
    return claim_order(worker_id=user_id, order_id=order_id)


@worker_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@jwt_required()
@role_required("worker")
def update_order_status_route(order_id, user_id, user_role):
    """
    Update the status of an order assigned to the worker.

    Args:
        order_id: The ID of the order being updated.

    Returns:
        JSON response confirming the status update or an error message.
    """
    data = request.json or {}

    status = data.get("status")
    if not status:
        return jsonify({"error": "Status is required"}), 400

    return update_order_status(
        worker_id=user_id,
        order_id=order_id,
        status=status
    )


@worker_bp.route("/create-order", methods=["POST"])
@jwt_required()
@role_required("worker")
def create_order_for_customer_route(user_id, user_role):
    """
    Create an order on behalf of a customer.

    Returns:
        JSON response with the created order details or an error message.
    """
    data = request.json or {}

    # Validate pickup and delivery times
    try:
        pickup_time = dateutil.parser.isoparse(data.get("pickup_time"))
        delivery_time = dateutil.parser.isoparse(data.get("delivery_time"))
    except Exception:
        return jsonify(
            {"error": "pickup_time and delivery_time "
                "must be ISO datetime strings"}
        ), 400

    customer_id = data.get("customer_id")
    price = data.get("price")

    # Check required fields
    if not customer_id or not price:
        return jsonify({"error": "customer_id and price are required"}), 400

    return create_order_for_customer(
        worker_id=user_id,
        customer_id=customer_id,
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        price=float(price)
    )
