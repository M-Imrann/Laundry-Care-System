from flask import jsonify
from database import db
from models import Order, OrderStatus, User, UserRole
from datetime import datetime, timezone, timedelta
from utils.exceptions_util import NotFoundError, ValidationError
from core.constants import constants
from zoneinfo import ZoneInfo


def cancel_order(user_id: int, order_id: int, role: UserRole):
    """
    Cancel order (admin or customer).
    - Customers can only cancel their own orders.
    - Admins can cancel any order.
    - Both follow pickup-time rules and cancellation fee logic.
    """

    # Fetch user
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("User not found")

    # Query order (differs for admin vs customer)
    filters = {"id": order_id}
    if role == UserRole.customer:
        filters["customer_id"] = user_id
    order = Order.query.filter_by(**filters).first()
    if not order:
        raise NotFoundError("Order not found")

    # Ensure pickup_time is UTC aware
    pickup_time = order.pickup_time
    if pickup_time.tzinfo is None:
        pakistan_tz = ZoneInfo("Asia/Karachi")
        pickup_time = pickup_time.replace(tzinfo=pakistan_tz)
        pickup_time = pickup_time.astimezone(timezone.utc)

    now = datetime.now(timezone.utc)

    # Restriction: cannot cancel after pickup
    if now > pickup_time:
        raise ValidationError(
            "Cannot cancel order after pickup time",
            field="pickup_time"
            )

    # Cancellation fee if within 1 hour
    cancellation_fee = 0.0
    if pickup_time - now <= timedelta(hours=1):
        cancellation_fee = (constants.fee_percentage / 100) * order.price

    # Update order
    order.status = OrderStatus.cancelled
    order.cancellation_fee = cancellation_fee
    db.session.commit()

    # Role-specific message
    msg = f"Order cancelled by {role} {user.name} (ID: {user.id})"

    return jsonify({
        "message": msg,
        "cancellation_fee": cancellation_fee
    }), 200
