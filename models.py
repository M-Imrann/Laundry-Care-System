import enum
from database import db
from datetime import datetime, timezone


class UserRole(enum.Enum):
    """
    Enum for different roles a user can have in the system.
    """
    customer = "customer"
    worker = "worker"
    admin = "admin"


class WorkerStatus(enum.Enum):
    """
    Enum for worker status.
    """
    active = "active"
    inactive = "inactive"


class OrderStatus(enum.Enum):
    """
    Enum for tracking different stages of an order lifecycle.
    """
    created = "created"
    claimed = "claimed"
    picked_up = "picked_up"
    in_progress = "in_progress"
    delivered = "delivered"
    completed = "completed"
    cancelled = "cancelled"


class User(db.Model):
    """
    Represents a user in the system.
    A user can be a customer, worker, or admin.
    """
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(db.String(80))
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )
    password = db.Column(
        db.String(120),
        nullable=False
    )
    phone = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )
    role = db.Column(
        db.Enum(UserRole),
        nullable=False,
        default=UserRole.customer
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc)
    )

    # A user can be linked to either a customer or a worker profile
    customer = db.relationship("Customer", backref="user", uselist=False)
    worker = db.relationship("Worker", backref="user", uselist=False)


class Worker(db.Model):
    """
    Represents a worker profile linked to a user.
    Workers can take and complete orders.
    """
    id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        primary_key=True,
        nullable=False
    )
    status = db.Column(
        db.Enum(WorkerStatus),
        nullable=False,
        default=WorkerStatus.inactive
    )
    performance_score = db.Column(
        db.Float,
        default=0.0
    )

    # Relationships Workers can have multiple orders and status history records
    orders = db.relationship("Order", backref="worker")
    status_history = db.relationship("WorkerStatusHistory", backref="worker")


class Customer(db.Model):
    """
    Represents a customer profile linked to a user.
    Customers place orders and have assigned workers and addresses.
    """
    id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        primary_key=True,
        nullable=False
    )
    assigned_worker_id = db.Column(
        db.Integer,
        db.ForeignKey('worker.id'),
        nullable=True
    )

    # Relationships: Customers can have multiple orders and addresses
    orders = db.relationship("Order", backref="customer")
    addresses = db.relationship("Address", backref="customer")


class Address(db.Model):
    """
    Stores customer addresses for pickup and delivery.
    A customer can have multiple addresses.
    """
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey('customer.id'),
        nullable=False
    )
    street = db.Column(
        db.String(200),
        nullable=False
    )
    city = db.Column(
        db.String(100),
        nullable=False
    )
    country = db.Column(
        db.String(100),
        default="Pakistan"
    )
    is_default = db.Column(
        db.Boolean,
        default=False
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc)
    )


class Order(db.Model):
    """
    Represents an order placed by a customer.
    Orders go through multiple stages from creation to completion.
    """
    id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False
    )
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey('customer.id'),
        nullable=False
    )
    worker_id = db.Column(
        db.Integer,
        db.ForeignKey('worker.id'),
        nullable=True
    )
    pickup_time = db.Column(
        db.DateTime,
        nullable=False
    )
    delivery_time = db.Column(
        db.DateTime,
        nullable=False
    )
    status = db.Column(
        db.Enum(OrderStatus),
        nullable=False
    )
    price = db.Column(
        db.Float,
        nullable=False
    )
    cancellation_fee = db.Column(
        db.Float,
        default=0.0
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.now(timezone.utc)
    )
    created_by = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc)
    )
    address_id = db.Column(
        db.Integer,
        db.ForeignKey('address.id'),
        nullable=False
    )

    # Relationship: Orders maintain a history of status changes
    status_history = db.relationship("OrderStatusHistory", backref="order")


class WorkerStatusHistory(db.Model):
    """
    Logs every status change of a worker.
    Useful for tracking worker availability and history.
    """
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    worker_id = db.Column(
        db.Integer,
        db.ForeignKey('worker.id'),
        nullable=False
    )
    status = db.Column(
        db.Enum(WorkerStatus),
        nullable=False
    )
    changed_by = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    changed_at = db.Column(
        db.DateTime,
        default=datetime.now(timezone.utc)
    )


class OrderStatusHistory(db.Model):
    """
    Tracks status changes of an order.
    Helps in auditing order progress and responsibility.
    """
    id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False
    )
    order_id = db.Column(
        db.Integer,
        db.ForeignKey('order.id'),
        nullable=False
    )
    status = db.Column(
        db.Enum(OrderStatus),
        nullable=False
    )
    status_changed_by = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    changed_at = db.Column(
        db.DateTime,
        default=datetime.now(timezone.utc)
    )


class CancellationPolicy(db.Model):
    """
    Defines cancellation rules for customers and workers.
    Example: If a customer cancels within X minutes, a fee is applied.
    """
    id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False
    )
    role = db.Column(
        db.Enum(UserRole),
        nullable=False
    )
    fee_percentage = db.Column(
        db.Float,
        nullable=False
    )
    applies_within_minutes = db.Column(
        db.Integer,
        nullable=False
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc)
    )
