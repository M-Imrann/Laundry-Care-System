from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from services.customer_service import (
    create_customer_address,
    create_order_for_customer,
    list_customer_orders
)
import dateutil
from utils.role_decorator_util import role_required
from utils.cancel_order_util import cancel_order


# Blueprint for customer-specific routes
customer_bp = Blueprint("customer_bp", __name__)


@customer_bp.route("/address", methods=["POST"])
@jwt_required()
@role_required("customer")
def add_address(user_id, user_role):
    """
    Add a new address for the customer.

    Returns:
        JSON response with the created address or an error message.
    """
    address_payload = request.json or {}

    street = address_payload.get("street")
    city = address_payload.get("city")
    country = address_payload.get("country", "Pakistan")
    is_default = address_payload.get("is_default", False)

    # Validate required fields
    required_fields = {
        "street": street,
        "city": city,
    }

    for field, value in required_fields.items():
        if not value:
            return jsonify(
                {"error": f"{field.capitalize()} is required.", "field": field}
            ), 400

    return create_customer_address(
        customer_id=user_id,
        street=street,
        city=city,
        country=country,
        is_default=is_default
    )


@customer_bp.route("/create-order", methods=["POST"])
@jwt_required()
@role_required("customer")
def create_order(user_id, user_role):
    """
    Create a new order for the customer.

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

    price = data.get("price")
    address_id = data.get("address_id")

    # Ensure required fields are present
    required_fields = {
        "pickup_time": pickup_time,
        "delivery_time": delivery_time,
        "address_id": address_id,
    }
    for field, value in required_fields.items():
        if not value:
            return jsonify(
                {"error": f"{field.capitalize()} is required.", "field": field}
            ), 400

    return create_order_for_customer(
        customer_id=user_id,
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        price=float(price),
        address_id=address_id
    )


@customer_bp.route("/list-orders", methods=["GET"])
@jwt_required()
@role_required("customer")
def list_orders(user_id, user_role):
    """
    Retrieve all orders created by the customer.

    Returns:
        JSON response with a list of the customer's orders.
    """
    return list_customer_orders(customer_id=user_id)


@customer_bp.route("/cancel-order/<int:order_id>", methods=["DELETE"])
@jwt_required()
@role_required("customer")
def cancel_order_route(order_id, user_id, user_role):
    """
    Cancel a specific order for the customer.

    Args:
        order_id: The ID of the order to cancel.

    Returns:
        JSON response confirming cancellation or an error message.
    """
    try:
        return cancel_order(
            user_id=user_id,
            order_id=order_id,
            role=user_role
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400
