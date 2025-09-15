from flask import jsonify
from database import db
from models import (
    Order,
    OrderStatus,
    Customer
)
from datetime import datetime
from utils.exceptions_util import ValidationError, NotFoundError


def list_unclaimed_orders():
    """
    Return all unclaimed orders.

    Unclaimed orders are those with status 'created'
    and no worker assigned yet.
    """
    orders = Order.query.filter_by(
        worker_id=None,
        status=OrderStatus.created
    ).all()

    # Build and return response list of available orders
    return jsonify([
        {
            "order_id": order.id,
            "pickup_time": order.pickup_time.isoformat(),
            "delivery_time": order.delivery_time.isoformat(),
            "price": order.price,
            "customer_id": order.customer_id
        } for order in orders
    ]), 200


def claim_order(worker_id: int, order_id: int):
    """
    Allow a worker to claim an unassigned order.

    - Finds an order with no assigned worker.
    - Assigns the worker_id to it.
    - Updates status to 'claimed'.
    """
    order = Order.query.filter_by(id=order_id, worker_id=None).first()
    if not order:
        raise NotFoundError("Order not available for claiming")

    # Assign worker and update status
    order.worker_id = worker_id
    order.status = OrderStatus.claimed
    db.session.commit()

    return jsonify(
        {
            "message": "Order claimed successfully",
            "order_id": order.id
        }
    ), 200


def update_order_status(worker_id: int, order_id: int, status: str):
    """
    Worker updates the status of their assigned order.

    Allowed transitions:
    Picked Up → In Progress → Delivered → Completed
    """
    # Fetch order assigned to worker
    order = Order.query.filter_by(id=order_id, worker_id=worker_id).first()
    if not order:
        raise NotFoundError("Order not found or not assigned to this worker")

    # Validate provided status string
    try:
        new_status = OrderStatus[status.lower()]
    except KeyError:
        raise ValidationError("Invalid status", field="status")

    # Update status
    order.status = new_status
    db.session.commit()

    return jsonify({
        "message": "Order status updated",
        "order_id": order.id,
        "status": order.status.value
    }), 200


def create_order_for_customer(
        worker_id: int,
        customer_id: int,
        pickup_time: datetime,
        delivery_time: datetime,
        price: float
        ):
    """
    Worker creates a new order for their assigned customer.

    - Ensures delivery_time is after pickup_time.
    - Verifies that the worker is assigned to the customer.
    - Creates a new order linked to the worker and customer.
    """
    # Validate pickup and delivery times
    if delivery_time <= pickup_time:
        raise ValidationError("Delivery time must be after pickup time")

    # Check worker-customer assignment
    customer = Customer.query.filter_by(
        id=customer_id,
        assigned_worker_id=worker_id
    ).first()
    if not customer:
        raise ValidationError("Customer not assigned to this worker")

    # Create order
    order = Order(
        customer_id=customer_id,
        worker_id=worker_id,
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        status=OrderStatus.created,
        price=price,
        created_by=worker_id,
        address_id=customer.addresses[0].id if customer.addresses else None
    )
    db.session.add(order)
    db.session.commit()

    return jsonify(
        {
            "message": "Order created by worker",
            "order_id": order.id
        }
    ), 201
