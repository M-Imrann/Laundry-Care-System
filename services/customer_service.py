from flask import jsonify
from database import db
from models import (
    Order,
    OrderStatus,
    Address
)
from datetime import datetime, timezone
from utils.exceptions_util import ValidationError


def create_customer_address(
        customer_id: int,
        street: str,
        city: str,
        country: str = "Pakistan",
        is_default: bool = False
        ):
    """
    Create and save a new address for a customer.

    Args:
        customer_id: ID of the customer.
        street: Street address.
        city: City name.
        country: Country name (default is "Pakistan").
        is_default: Whether the address is the default address.

    Returns:
        JSON response with success message and address ID.
    """
    address = Address(
         customer_id=customer_id,
         street=street,
         city=city,
         country=country,
         is_default=is_default
    )

    db.session.add(address)
    db.session.commit()

    return jsonify({
        "message": "Address added Successfully.",
        "address_id": address.id
    }), 201


def create_order_for_customer(
        customer_id: int,
        pickup_time: datetime,
        delivery_time: datetime,
        price: float,
        address_id: int
        ):
    """
    Create a new order for a customer.

    Args:
        customer_id: ID of the customer creating the order.
        pickup_time: Datetime when order should be picked up.
        delivery_time: Datetime when order should be delivered.
        price: Price of the order.
        address_id: Address linked to the order.

    Returns:
        JSON response with success message and created order ID.

    Raises:
        ValidationError: If pickup or delivery times are invalid.
    """
    now = datetime.now(timezone.utc)

    # Ensure pickup_time and delivery_time are timezone-aware
    if pickup_time.tzinfo is None:
        pickup_time = pickup_time.replace(tzinfo=timezone.utc)
    if delivery_time.tzinfo is None:
        delivery_time = delivery_time.replace(tzinfo=timezone.utc)

    # Validate times
    if pickup_time <= now:
        raise ValidationError(
            "Pickup time must be in the future",
            field="pickup_time"
        )
    if delivery_time <= pickup_time:
        raise ValidationError(
            "Delivery time must be after pickup time",
            field="delivery_time"
        )

    # Create and persist new order
    order = Order(
        customer_id=customer_id,
        worker_id=None,
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        status=OrderStatus.created,
        price=price,
        created_by=customer_id,
        address_id=address_id
    )
    db.session.add(order)
    db.session.commit()

    return jsonify({
        "message": "Order created successfully",
        "order_id": order.id
    }), 201


def list_customer_orders(customer_id: int):
    """
    List all orders for a specific customer.

    Orders are sorted by creation date (newest first).

    Args:
        customer_id: ID of the customer.

    Returns:
        JSON response with list of orders containing:
            - order_id
            - pickup_time
            - delivery_time
            - status
            - price
            - worker_id
    """
    # Fetch all orders for the given customer
    orders = Order.query.filter_by(
        customer_id=customer_id
    ).order_by(Order.created_at.desc()).all()

    # Convert orders into list of dictionaries
    orders_list = []
    for order in orders:
        orders_list.append({
            "order_id": order.id,
            "pickup_time": order.pickup_time.isoformat(),
            "delivery_time": order.delivery_time.isoformat(),
            "status": order.status.value,
            "price": order.price,
            "worker_id": order.worker_id
        })

    return jsonify(orders_list), 200
